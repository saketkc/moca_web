from models import Job, EncodeData
from database import db_session
import datetime

"""
job
+-----------------+--------------+------+-----+---------+-------+
| Field           | Type         | Null | Key | Default | Extra |
+-----------------+--------------+------+-----+---------+-------+
| job_id          | varchar(80)  | NO   | PRI | NULL    |       |
| async_id        | varchar(80)  | NO   | PRI | NULL    |       |
| filename        | varchar(200) | YES  |     | NULL    |       |
| job_metadata    | text         | YES  |     | NULL    |       |
| created_at      | datetime     | YES  |     | NULL    |       |
| last_updated_at | datetime     | YES  |     | NULL    |       |
| status          | varchar(40)  | YES  |     | NULL    |       |
| exception_log   | varchar(200) | YES  |     | NULL    |       |
| client_ip       | varchar(20)  | YES  |     | NULL    |       |
+-----------------+--------------+------+-----+---------+-------+

encodedata
+-----------------+-------------+------+-----+---------+-------+
| Field           | Type        | Null | Key | Default | Extra |
+-----------------+-------------+------+-----+---------+-------+
| peakfile_id     | varchar(40) | NO   | PRI | NULL    |       |
| dataset_id      | varchar(40) | YES  |     | NULL    |       |
| run_job_id      | varchar(80) | YES  | MUL | NULL    |       |
| encode_metadata | text        | YES  |     | NULL    |       |
+-----------------+-------------+------+-----+---------+-------+
"""
def insert_new_job(job_id, async_id, filename=None, client_ip=None):
    job = Job(job_id=str(job_id), async_id=str(async_id), filename=filename, client_ip=client_ip)
    db_session.add(job)
    db_session.commit()

def insert_encode_job(peakfile_id, dataset_id, run_job_id, encode_metadata):
    encodedata = EncodeData(peakfile_id=peakfile_id,
                            dataset_id=dataset_id,
                            run_job_id=run_job_id,
                            encode_metadata=encode_metadata)
    db_session.add(encodedata)
    db_session.commit()

def update_job_status(job_id, result, exception_log=None):
    job = Job.query.filter_by(job_id=job_id).first()
    job.last_updated_at = datetime.datetime.now()
    job.status = result
    job.exception_log = exception_log
    db_session.commit()

def get_job_status(job_id):
    job = Job.query.filter_by(job_id=job_id).first()
    return{'status': job.status, 'exception_log': job.exception_log}

def encode_job_exists(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    if query:
        return True
    return False

def encode_job_status(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    if not query:
        return 'inexistent'
    job = Job.query.filter_by(job_id=query.run_job_id).first()
    if job:
        return job.status
    return 'inexistent'

def get_encode_jobid(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    return query.run_job_id


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

def get_job_metadata(job_id):
    query = Job.query.filter_by(job_id=job_id).first()
    if query:
        return query.job_metadata
    return None

def get_encode_metadata(peakfile_id):
    query = EncodeData.query.filter_by(peakfile_id=peakfile_id).first()
    return query.encode_metadata

def get_filename(async_id):
    query = Job.query.filter_by(async_id=async_id).first()
    if query:
        return query.filename
    return None

def job_exists(job_id):
    query = Job.query.filter_by(job_id=job_id).first()
    if query:
        return True
    return False

