#!/usr/bin/env python
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from uuid import uuid4
from celery import Celery
from peaks_processor_celery import run_conservation_analysis, run_motif_analysis, run_analysis
from flask.ext.sqlalchemy import SQLAlchemy
import shutil
import json
from celery import group
from config_processor import read_config
from encode_peak_file_downloader import get_encode_peakfiles, get_metadata_for_peakfile
import subprocess
from bed_operations.format_peakfile import convert_to_scorefile
from query import get_async_id, encode_job_exists, insert_encode_job, update_job_status, insert_new_job, get_encode_metadata, get_filename, insert_job_tracking
from database import SqlAlchemyTask
import operator

server_config = read_config('Server')
path_config = read_config('StaticPaths')


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = server_config['celery_broker_url']
app.config['CELERY_RESULT_BACKEND'] = server_config['celery_result_backend']
app.config['SQLALCHEMY_DATABASE_URI'] = server_config['sqlalchemy_database_uri']
app.config['CELERYD_MAX_TASKS_PER_CHILD'] = server_config['celery_max_tasks_per_child']
app.config['CELERY_IMPORTS'] = ('app',)
app.config['CELERYD_TASK_TIME_LIMIT'] = 1000000
app.url_map.strict_slashes = False

db = SQLAlchemy(app)
celery = Celery('app', broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


UPLOAD_FOLDER = path_config['job_upload_path']
STATIC_PATH = path_config['job_render_path']
ENCODE_BASE_URL = path_config['encode_base_url']

param_config = read_config('Parameters')

N_MEME_MOTIFS = int(param_config['n_meme_motifs'])

class SubmitJob(object):
    def __init__(self):
        self.job_id = str(uuid4())
        self.error = 'No'


@celery.task(bind=True)
def run_motif_analysis_job(self, data):
    job_id = data['job_id']
    genome = data['genome']
    #run_analysis(job_id, genome)
    encoder_object = run_motif_analysis(job_id, genome)
    return encoder_object


@celery.task(bind=True, base=SqlAlchemyTask)
def run_job(self, data):
    job_id = data['job_id']
    genome = data['genome']
    result = run_analysis(job_id, genome)
    if result == 'success':
        update_job_status(job_id, 'success')
    else:
        update_job_status(job_id, 'failure')


@celery.task(bind=True, base=SqlAlchemyTask)
def run_encode_job(self, data):
    dataset_id = data['dataset_id']
    peakfile_id = data['peakfile_id']
    genome = data['genome']
    job_id = data['job_id']
    metadata = data['metadata']
    result = run_analysis(job_id, genome)

    if result:
        insert_encode_job(peakfile_id, dataset_id, metadata)
        post_process_encode_job(job_id, dataset_id, peakfile_id)
    else:
        #TODO Log the error
        pass


@celery.task(bind=True)
def run_conservation_analysis_job(self, encoder_object, motif):
    #encoder_object = data['encoder_object']
    #motif = data['motif']
    return run_conservation_analysis(encoder_object, motif)


@celery.task(bind=True)
def parallel_conservation_analysis(self, encoder_object):
    return group(run_conservation_analysis_job(encoder_object, i) for i in range(1, encoder_object.total_motifs+1))


workflow = (run_motif_analysis_job.s() | group(run_conservation_analysis_job.s(motif) for motif in range(1,4)))


@app.route('/', methods=['GET', 'POST'])
def upload_file(metadata=None):
    if request.method == 'POST':
        job = SubmitJob()
        job_id = job.job_id
        ## Create directory to run job
        job_folder = os.path.join(UPLOAD_FOLDER, job_id)
        os.makedirs(job_folder)
        if metadata is None:
            file = request.files['file']
            ## Hard code all incoming files to peaks.tsv
            filename = file.filename
            user_filepath = os.path.join(job_folder, filename)
            file.save(user_filepath)
            peak_filepath = os.path.join(job_folder, 'peaks.tsv')
            convert_to_scorefile(user_filepath, filetype=None, out_file=peak_filepath)
            genome = request.form['genome']
        else:
            href = metadata['href']
            file_type = metadata['output_type']
            filepath = os.path.join(job_folder, href.split('/')[-1])
            subprocess.call(["wget", "-c", href, "-P", job_folder])
            subprocess.call(["gunzip", filepath])
            convert_to_scorefile(filepath, file_type)
            genome = metadata['assembly']


        data = {'job_id': job_id, 'genome': genome}
        async_id = run_job.apply_async([data], )
        #group_id = workflow.apply_async([data])
        #async_id = group_id.id
        #async_id = run_motif_analysis_job.apply_async([data], link=parallel_conservation_analysis.s())
        insert_new_job(async_id, job_id, str(file.filename))
        client_ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
        insert_job_tracking(job_id, client_ip)
        return redirect(url_for('results', job_id=job_id))
    elif request.method == 'GET':
        return render_template('index.html')


def post_process(async_id, job_id):
    source_path = os.path.join(STATIC_PATH, async_id)
    destination_path = os.path.join(STATIC_PATH, job_id)
    try:
        shutil.move(source_path, destination_path)
    except:
        pass


def post_process_encode_job(job_id, dataset_id, peakfile_id):
    #async_id = get_async_id(job_id)
    source_path = os.path.join(STATIC_PATH, job_id)
    destination_path = os.path.join(STATIC_PATH, 'encode', dataset_id, peakfile_id)
    try:
        shutil.move(source_path, destination_path)
    except:
        pass


def read_summary(job_id):
    path = os.path.join(STATIC_PATH, job_id, 'summary.json')
    with open(path) as data_file:
        data = json.load(data_file)
    return data


@app.route('/status/<job_id>')
def job_status(job_id):
    async_id = get_async_id(job_id)
    dataset_id = request.args.get('dataset_id')
    peakfile_id = request.args.get('peakfile_id')
    if dataset_id:
        job = run_encode_job.AsyncResult(async_id)
    else:
        job = run_job.AsyncResult(async_id)
    #job = workflow.AsyncResult(async_id)
    #job = run_motif_analysis_job.AsyncResult(async_id)
    if job.state == 'PENDING':
        return json.dumps({'status': 'pending', 'job_id':job_id})
    else:
        #post_process(async_id, job_id)
        images = ['motif{}Combined_plots.png'.format(i) for i in range(1, N_MEME_MOTIFS+1)]
        if dataset_id:
            metadata = json.loads(get_encode_metadata(peakfile_id))
            summary = read_summary('encode/{}/{}'.format(dataset_id, peakfile_id))
            motif_occurrences=summary['motif_occurrences']
            peaks = summary['peaks']
            sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
            images = ['/static/jobs/encode/{}/{}/{}Combined_plots.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
        else:
            images = ['/static/jobs/{}/{}'.format(job_id, i) for i in images]

            summary = read_summary(job_id)
            motif_occurrences=summary['motif_occurrences']
            peaks = summary['peaks']
            sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
            images = ['/static/jobs/encode/{}/{}/{}Combined_plots.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
            metadata = {'filename': get_filename(async_id)}
        print metadata
        """
        return json.dumps({'status': job.status,
                           'job_id':job_id,
                           'motifs':images,
                           'motif_occurrences': summary['motif_occurrences'],
                           'metadata': metadata,
                           'peaks': summary['peaks'] })

        """
        return jsonify(status=job.status,
                       job_id=job_id,
                       motifs=images,
                       motif_occurrences=dict(sorted_mo),
                       metadata=metadata,
                       peaks=summary['peaks'])
@app.route('/results/<job_id>')
def results(job_id):
    async_id = get_async_id(job_id)
    if async_id:
        return render_template('results.html', job_id=job_id)
    else:
        return json.dumps({'message': 'error locating job:'})


@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'GET':
        return render_template('encode.html')
    else:
        data = request.json
        encode_id = data['encodeid']
        encode_peakfiles = get_encode_peakfiles(encode_id)
        if type(encode_peakfiles) == 'dict' and 'status' in encode_peakfiles.keys():
            return json.dumps({'status': 'error', 'response': encode_peakfiles})
        return json.dumps({'peak_files': encode_peakfiles})


@app.route('/encodejob/<dataset_id>/<peakfile_id>')
def encodejobs(dataset_id, peakfile_id):
    if encode_job_exists(peakfile_id):
        print 'Exists'
        #images = ['motif{}Combined_plots.png'.format(i) for i in range(1, N_MEME_MOTIFS+1)]
        #images = ['/static/jobs/encode/{}/{}/{}'.format(dataset_id, peakfile_id, i) for i in images]
        summary = read_summary('encode/{}/{}'.format(dataset_id, peakfile_id))
        metadata = json.loads(get_encode_metadata(peakfile_id))
        motif_occurrences=summary['motif_occurrences']
        peaks = summary['peaks']
        sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
        images = {i:'/static/jobs/encode/{}/{}/{}Combined_plots.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1}
        data = ({'motifs':images, 'motif_occurrences': summary['motif_occurrences'], 'peaks': summary['peaks'] })
        return render_template('encoderesults.html', job_id='none', data=data, metadata=(metadata))#motifs=images, motif_occurrences=summary['motif_occurrences'], peaks=summary['peaks'], job_id='none')
    metadata = get_metadata_for_peakfile(dataset_id, peakfile_id)
    if type(metadata) == 'dict' and 'status' in metadata.keys():
        return json.dumps({'status': 'error', 'response': metadata})
    job = SubmitJob()
    job_id = job.job_id
    ## Create directory to run job
    job_folder = os.path.join(UPLOAD_FOLDER, job_id)
    if not os.path.exists(job_folder):
        os.makedirs(job_folder)
    href = metadata['href']
    file_type = metadata['file_type']
    filepath = os.path.join(job_folder, href.split('/')[-1])
    subprocess.call(["wget", "-c", href, "-P", job_folder])
    subprocess.call(["gunzip", filepath])
    convert_to_scorefile(filepath.replace('.gz',''), file_type)
    genome = metadata['assembly']


    data = {'job_id': job_id, 'genome': genome, 'dataset_id': dataset_id, 'peakfile_id': peakfile_id, 'metadata': metadata}
    async_id = run_encode_job.apply_async([data], )
    insert_new_job(async_id, job_id)
    client_ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    insert_job_tracking(job_id, client_ip)
    return render_template('encoderesults.html', job_id=job_id, dataset_id=dataset_id, peakfile_id=peakfile_id, data=json.dumps({}), metadata=json.dumps(metadata))



if __name__ == '__main__':
    app.run(host=server_config['host'], debug=True)
