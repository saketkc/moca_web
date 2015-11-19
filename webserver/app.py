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
from query import get_async_id, encode_job_exists, insert_encode_job, update_job_status, insert_new_job, get_encode_metadata, get_filename, get_job_status, job_exists, encode_job_status, get_encode_jobid, is_job_type_encode,get_encode_from_jobid, get_all_encode_results
from database import SqlAlchemyTask
import operator
from Bio import motifs
jaspar_motifs = motifs.parse(open('../data/pfm_vertebrates.txt'), 'jaspar')

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
        if metadata is None:
            self.file = request.files['file']
            self.filename = str(self.file.filename)
            assert self.filename!=''
            self.user_filepath = os.path.join(self.job_folder, self.filename)
        else:
            self.filename = metadata['title']
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
            print 'Error creating folder: {}'.format(self.job_folder)
            raise RuntimeError('Error creating job directory')

        if self.metadata is None:
            self.file.save(self.user_filepath)
            peak_filepath = os.path.join(self.job_folder, 'peaks.tsv')
            convert_to_scorefile(self.user_filepath,filetype=None, out_file=peak_filepath)
        else:
            self.genome = self.metadata['assembly']
            href = self.metadata['href']
            filepath = os.path.join(self.job_folder, href.split('/')[-1])
            retcode = subprocess.call(['wget', '-c', href, '-P', self.job_folder])
            if int(retcode)!=0:
                raise RuntimeError('Error downloading peak file from Encode')
            retcode = subprocess.call(['gunzip', filepath])
            if int(retcode)!=0:
                raise RuntimeError('Error extracting zip archive')
            filepath = filepath.replace('.gz','')
            convert_to_scorefile(filepath)


        data = {'job_id': self.job_id, 'genome': self.genome, 'metadata': self.metadata}
        self.async_id = run_job.apply_async([data], )
        insert_new_job(self.job_id, self.async_id, self.filename, self.client_ip)
        if self.metadata:
            dataset_id = self.metadata['dataset']
            peakfile_id = self.metadata['title']
            insert_encode_job(peakfile_id, dataset_id, self.job_id, self.metadata)

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
    metadata = data['metadata']
    try:
        run_analysis(job_id, genome, metadata)
        exception_log = None
        result ='success'
    except RuntimeError as e:
        result ='failure'
        args = e.args
        for x in args:
            print x
        print args[1][1]
        exception_log = {'message': args[0], 'stdout': args[1][1], 'stderr': args[1][2]}
        exception_log = json.dumps(exception_log)
    update_job_status(job_id, result, exception_log)
    print '**************UPDATE******************************'
    if metadata:
        print metadata
        print '**************UPDATE******************************'
        dataset_id = metadata['dataset']
        peakfile_id = metadata['title']
        #insert_encode_job(peakfile_id, dataset_id, job_id, metadata)
        print '**************UPDATE******************************'
        post_process_encode_job(job_id, dataset_id, peakfile_id)

@celery.task(bind=True)
def run_conservation_analysis_job(self, encoder_object, motif):
    #encoder_object = data['encoder_object']
    #motif = data['motif']
    return run_conservation_analysis(encoder_object, motif)


@celery.task(bind=True)
def parallel_conservation_analysis(self, encoder_object):
    return group(run_conservation_analysis_job(encoder_object, i) for i in range(1, encoder_object.total_motifs+1))


workflow = (run_motif_analysis_job.s() | group(run_conservation_analysis_job.s(motif) for motif in range(1,4)))

def process_job(request, metadata):
    job = ProcessJob(request,metadata)
    try:
        job.submit()
        return job
    except RuntimeError as e:
        print e
        raise RuntimeError('Error:{}'.format(e))


@app.route('/', methods=['GET', 'POST'])
def upload_file(metadata=None):
    if request.method == 'GET':
        return render_template('index.html')
    else:
        job = process_job(request, metadata)
        if request.form['format']=='json':
            return jsonify(job_id=job.job_id)
        if metadata is None:
            return redirect(url_for('results', job_id=job.job_id))


def post_process(async_id, job_id):
    source_path = os.path.join(STATIC_PATH, async_id)
    destination_path = os.path.join(STATIC_PATH, job_id)
    try:
        shutil.move(source_path, destination_path)
    except Exception as e:
        #os.remove(destination_path)
        #shutil.move(source_path, destination_path)
        raise RuntimeError('Error moving directory: {}'.format(e))


def post_process_encode_job(job_id, dataset_id, peakfile_id):
    #async_id = get_async_id(job_id)
    source_path = os.path.join(STATIC_PATH, job_id)
    destination_path = os.path.join(STATIC_PATH, 'encode', dataset_id, peakfile_id)
    try:
        shutil.move(source_path, destination_path)
    except:
        os.removedirs(destination_path)
        shutil.move(source_path, destination_path)


def read_summary(job_id):
    path = os.path.join(STATIC_PATH, job_id, 'summary.json')
    with open(path) as data_file:
        data = json.load(data_file)
    return data

@app.route('/encodeanalysis')
def encode_analysis():
    results = get_all_encode_results()
    data = []
    for result in results:
        metadata = json.loads(result.encode_metadata)
        obj = {'dataset_id':result.dataset_id,
               'peakfile_id':result.peakfile_id,
               'transcription_factor':metadata['gene_name'],
               'technical_replicate':metadata['tech_repl_number'],
               'biological_replicate':metadata['bio_repl_number'],
               'file_type':metadata['file_type']
               }
        data.append(json.dumps(obj))
    return render_template('encodeanalysis.html', results=map(json.loads, data))

@app.route('/status/<job_id>')
def job_status(job_id):
    is_job_in_db =job_exists(job_id)
    if not is_job_in_db:
        return jsonify(status='failure', message='Unable to locate job')

    async_id = get_async_id(job_id)
    dataset_id = None #request.args.get('dataset_id')
    peakfile_id = None # request.args.get('peakfile_id')
    if is_job_type_encode(job_id):
        data = get_encode_from_jobid(job_id)
        dataset_id = data['dataset_id']
        peakfile_id = data['peakfile_id']
    job_db = get_job_status(job_id)
    status = job_db['status']
    job = run_job.AsyncResult(async_id)
    #job = workflow.AsyncResult(async_id)
    #job = run_motif_analysis_job.AsyncResult(async_id)
    print 'JOB STATE: {}'.format(job.state)

    if status == 'pending':
        return json.dumps({'status': 'pending', 'job_id':job_id})
    elif status == 'success':
        #post_process(async_id, job_id)
        images = ['motif{}Combined_plots.png'.format(i) for i in range(1, N_MEME_MOTIFS+1)]
        if dataset_id:
            metadata = json.loads(get_encode_metadata(peakfile_id))
            summary = read_summary('encode/{}/{}'.format(dataset_id, peakfile_id))
            motif_occurrences=summary['motif_occurrences']
            peaks = summary['peaks']
            sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
            motifs = [i for i,j in sorted_mo if float(j)/peaks>0.1]
            images = ['/static/jobs/encode/{}/{}/{}Combined_plots.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
            rcimages = ['/static/jobs/encode/{}/{}/{}Combined_plots_rc.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
        else:
            summary = read_summary(job_id)
            motif_occurrences=summary['motif_occurrences']
            peaks = summary['peaks']
            sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
            images = {i:'/static/jobs/{}/{}Combined_plots.png'.format(job_id, i) for i,j in sorted_mo if float(j)/peaks>0.1}
            motifs = [i for i,j in sorted_mo if float(j)/peaks>0.1]
            #images = ['/static/jobs/{}/{}Combined_plots.png'.format(job_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
            rcimages = {i:'/static/jobs/{}/{}Combined_plots_rc.png'.format(job_id, i) for i,j in sorted_mo if float(j)/peaks>0.1}
            #rcimages = ['/static/jobs/{}/{}Combined_plots_rc.png'.format(job_id, i) for i,j in sorted_mo if float(j)/peaks>0.1]
            metadata = {'filename': get_filename(async_id)}
        return jsonify(status=job.status,
                       job_id=job_id,
                       motifs=motifs,
                       images=images,
                       rcimages=rcimages,
                       motif_occurrences=dict(sorted_mo),
                       metadata=metadata,
                       peaks=summary['peaks'])
    else:
        exception_log = job_db['exception_log']
        if not exception_log:
            exception_log="{'stderr':'none', 'stdlog':'none', 'output':'none'}"
        status = 'failure'
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

@app.route('/encodejob/<dataset_id>/<peakfile_id>', methods=['GET', 'POST'])
def encodejobs(dataset_id, peakfile_id):
    job_status = encode_job_status(peakfile_id)
    if job_status == 'success':
        summary = read_summary('encode/{}/{}'.format(dataset_id, peakfile_id))
        metadata = json.loads(get_encode_metadata(peakfile_id))
        motif_occurrences=summary['motif_occurrences']
        peaks = summary['peaks']
        sorted_mo = sorted(motif_occurrences.items(), key=operator.itemgetter(1), reverse=True)
        images = {i:'/static/jobs/encode/{}/{}/{}Combined_plots.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1}
        rcimages = {i:'/static/jobs/encode/{}/{}/{}Combined_plots_rc.png'.format(dataset_id, peakfile_id, i) for i,j in sorted_mo if float(j)/peaks>0.1}
        data = ({'motifs':images, 'motif_occurrences': summary['motif_occurrences'], 'peaks': summary['peaks'], 'rcimages':rcimages })
        if request.method=='POST':
            job_id = get_encode_jobid(peakfile_id)
            return jsonify(job_id=job_id,
                           dataset_id=dataset_id,
                           peakfile_id=peakfile_id,
                           data=data)
        return render_template('encoderesults.html', job_id='none', data=data, metadata=(metadata))#motifs=images, motif_occurrences=summary['motif_occurrences'], peaks=summary['peaks'], job_id='none')
    elif job_status == 'pending':
        metadata = get_metadata_for_peakfile(dataset_id, peakfile_id)
        job_id = get_encode_jobid(peakfile_id)
        if request.method=='GET':
            return render_template('encoderesults.html', job_id=job_id, dataset_id=dataset_id, peakfile_id=peakfile_id, data=json.dumps({}), metadata=json.dumps(metadata))
        else:
            return jsonify(job_id=job_id,
                           dataset_id=dataset_id,
                           peakfile_id=peakfile_id)
    elif job_status == 'inexistent':
        metadata = get_metadata_for_peakfile(dataset_id, peakfile_id)
        job = process_job(request, metadata)
        if request.method=='GET':
            return render_template('encoderesults.html', job_id=job.job_id, dataset_id=dataset_id, peakfile_id=peakfile_id, data=json.dumps({}), metadata=json.dumps(metadata))
        else:
            return jsonify(job_id=job.job_id,
                           dataset_id=dataset_id,
                           peakfile_id=peakfile_id)


    elif job_status == 'error':
        return json.dumps({'status': 'error', 'response': metadata})
    #if type(metadata) == 'dict' and 'status' in metadata.keys():
    #    return json.dumps({'status': 'error', 'response': metadata})
    #job = process_job(request, metadata)
    #return render_template('encoderesults.html', job_id=job.job_id, dataset_id=dataset_id, peakfile_id=peakfile_id, data=json.dumps({}), metadata=json.dumps(metadata))

@app.route('/jaspar/<tf_name>')
def jasper_search(tf_name):
    for m in jaspar_motifs:
        if m.name.lower() == tf_name.lower():
            fn = os.path.join(STATIC_PATH, 'logos', m.name+'.png')
            m.weblogo(fn,  show_errorbars=False, logo_title=m.name,  show_fineprint=False , symbols0='A', symbols1='T', symbols2='C', symbols3='G',
                      color0='red', color1='green', color2='blue', color3='orange')
            return jsonify(path=m.name+'.png', status='success')
    return jsonify(status='error')


if __name__ == '__main__':
    app.run(host=server_config['host'], debug=True)
