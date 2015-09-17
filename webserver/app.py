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
from query import get_async_id, encode_job_exists, insert_encode_job, update_job_status, insert_new_job, get_encode_metadata, get_filename, get_job_status, job_exists
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

def get_unique_job_id():
    return str(uuid4())

def get_client_ip(request):
    client_ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    return client_ip

class ProcessJob(object):
    def __init__(self,request, metadata):
        self.job_id = get_unique_job_id()
        self.job_folder = os.path.join(UPLOAD_FOLDER, self.job_id)
        self.file = request.files['file']
        self.filename = str(self.file.filename)
        assert self.filename!=''
        self.user_filepath = os.path.join(self.job_folder, self.filename)
        self.metadata = metadata
        self.client_ip = get_client_ip(request)
        self.genome = None
        self.async_id = None
        if metadata is None:
            self.genome = request.form['genome']

    def submit(self):
        try:
            os.makedirs(self.job_folder)
        except:
            # Error saving files
            raise RuntimeError('Error creating job directory')

        if self.metadata is None:
            self.file.save(self.user_filepath)
            peak_filepath = os.path.join(self.job_folder, 'peaks.tsv')
            convert_to_scorefile(self.user_filepath, filetype=None, out_file=peak_filepath)
        else:
            self.genome = self.metadata['assembly']
            href = self.metadata['href']
            file_type = self.metadata['output_type']
            filepath = os.path.join(self.job_folder, href.split('/')[-1])
            retcode = subprocess.call(['wget', '-c', href, '-P', self.job_folder])
            if int(retcode)!=0:
                raise RuntimeError('Error downloading peak file from Encode')
            retcode = subprocess.call(['gunzip', filepath])
            if int(retcode)!=0:
                raise RuntimeError('Error extracting zip archive')
            convert_to_scorefile(filepath, file_type)


        data = {'job_id': self.job_id, 'genome': self.genome}
        self.async_id = run_job.apply_async([data], )
        insert_new_job(self.job_id, self.async_id, self.filename, self.client_ip)

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
    try:
        run_analysis(job_id, genome)
        exception_log = None
        result ='success'
    except RuntimeError as e:
        result ='failure'
        args = e.args
        print 'LENGTH: {}'.format(len(args))
        for x in args:
            print x
        print args[1][1]
        exception_log = {'message': args[0], 'stdout': args[1][1], 'stderr': args[1][2]}
        exception_log = json.dumps(exception_log)
    update_job_status(job_id, result, exception_log)


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
        job = ProcessJob(request,metadata)
        try:
            job.submit()
        except RuntimeError as e:
            print e
            return str(e)
        if metadata is None:
            return redirect(url_for('results', job_id=job.job_id))
        else:
            return job
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
    is_job_in_db =job_exists(job_id)
    if not is_job_in_db:
        return jsonify(status='failure', message='Unable to locate job')

    async_id = get_async_id(job_id)
    dataset_id = request.args.get('dataset_id')
    peakfile_id = request.args.get('peakfile_id')
    job_db = get_job_status(job_id)
    status =job_db['status']
    if dataset_id:
        job = run_encode_job.AsyncResult(async_id)
    else:
        job = run_job.AsyncResult(async_id)
    #job = workflow.AsyncResult(async_id)
    #job = run_motif_analysis_job.AsyncResult(async_id)
    print 'JOB STATE: {}'.format(job.state)

    if status == 'pending':
        return json.dumps({'status': 'pending', 'job_id':job_id})
    elif status == 'SUCCESS':
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
        return jsonify(status=job.status,
                       job_id=job_id,
                       motifs=images,
                       motif_occurrences=dict(sorted_mo),
                       metadata=metadata,
                       peaks=summary['peaks'])
    else:
        exception_log = job_db['exception_log']
        return jsonify(status=status, message=json.loads(exception_log))
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
    job = upload_file(metadata)
    return render_template('encoderesults.html', job_id=job.job_id, dataset_id=dataset_id, peakfile_id=peakfile_id, data=json.dumps({}), metadata=json.dumps(metadata))



if __name__ == '__main__':
    app.run(host=server_config['host'], debug=True)
