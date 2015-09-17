import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import json

class Job(Base):
    """
    async_id => To check status of running jobs
    job_id => Folder name where jobs are run
    """
    __tablename__ = 'job'
    job_id = Column(String(80), primary_key=True, unique=True)
    async_id = Column(String(80), primary_key=True, unique=True)
    filename = Column(String(200))
    job_metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated_at = Column(DateTime(timezone=True), onupdate=datetime.datetime.now)
    status = Column(String(40), default='pending')
    exception_log = Column(Text, default=None)
    encodejob = relationship('EncodeData', backref='job', uselist=False, lazy='select')
    client_ip = Column(String(20))

    def __init__(self, async_id=None, job_id=None, filename=None, client_ip=None, job_metadata=None):
        self.async_id = async_id
        self.job_id = job_id
        self.filename = filename
        self.client_ip = client_ip
        self.job_metadata = json.dumps(job_metadata)

    def __repr__(self):
        return  '<Async_id: {}>'.format(self.async_id)

class EncodeData(Base):
    __tablename__ = 'encodedata'
    peakfile_id = Column(String(40), primary_key=True)
    dataset_id = Column(String(40))
    run_job_id = Column(String(80), ForeignKey('job.job_id'))
    encode_metadata = Column(Text)

    def __init__(self, peakfile_id=None, dataset_id=None, job_id=None, encode_metadata=None):
        self.peakfile_id = peakfile_id
        self.dataset_id = dataset_id
        self.job_id = job_id
        self.encode_metadata = json.dumps(encode_metadata)

    def __repr__(self):
        return '<Peakfile {}>'.format(self.peakfile_id)

