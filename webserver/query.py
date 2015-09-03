from models import Job, EncodeData, Tracker
from database import db_session
import datetime


def encode_job_exists(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    if query:
        return True
    else:
        return False

def insert_encode_job(peakfile_id, dataset_id, metadata):
    encodedata = EncodeData(peakfile_id=peakfile_id, dataset_id=dataset_id, file_metadata=metadata)
    db_session.add(encodedata)
    db_session.commit()

def insert_new_job(async_id, job_id, filename=None):
    job = Job(async_id=str(async_id), job_id=str(job_id), filename=filename)
    db_session.add(job)
    db_session.commit()

def insert_job_tracking(job_id, client_ip):
    query = Tracker(job_id=job_id, client_ip=client_ip)
    db_session.add(query)
    db_session.commit()

def get_job_id(async_id):
    query = Job.query.filter_by(async_id=async_id).first()
    if query:
        return query.job_id
    return None

def get_async_id(job_id):
    query = Job.query.filter_by(job_id=job_id).first()
    if query:
        return query.async_id
    return None

def update_job_status(job_id, result):
    job = Job.query.filter_by(job_id=job_id).first()
    job.completed_at = datetime.datetime.now()
    job.status = result
    db_session.commit()


def get_encode_metadata(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    return query.file_metadata

def get_filename(async_id):
    query = Job.query.filter_by(async_id=async_id).first()
    if query:
        return query.filename
    return None

