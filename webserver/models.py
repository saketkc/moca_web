import datetime
from sqlalchemy import Column, String, DateTime, Text
from database import Base
import json

class Job(Base):
    """
    async_id => To check status of running jobs
    job_id => Folder name where jobs are run
    """
    __tablename__ = 'job'
    async_id = Column(String(80), primary_key=True)
    job_id = Column(String(80), primary_key=True)
    filename = Column(String(200))
    job_metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), onupdate=datetime.datetime.now)
    status = Column(String(40), default='pending')

    def __init__(self, async_id=None, job_id=None, filename=None, job_metadata=None):
        self.async_id = async_id
        self.job_id = job_id
        self.filename = filename
        self.job_metadata = json.dumps(job_metadata)

    def __repr__(self):
        return  '<Async_id: {}>'.format(self.async_id)

class EncodeData(Base):
    __tablename__ = 'encodedata'
    peakfile_id = Column(String(40), primary_key=True)
    dataset_id = Column(String(40))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    file_metadata = Column(Text)


    def __init__(self, peakfile_id=None, dataset_id=None, file_metadata=None):
        self.peakfile_id = peakfile_id
        self.dataset_id = dataset_id
        self.file_metadata = json.dumps(file_metadata)

    def __repr__(self):
        return '<Peakfile {}>'.format(self.peakfile_id)

class Tracker(Base):
    __tablename__ = 'tracker'
    job_id = Column(String(80), primary_key=True)
    client_ip = Column(String(80))

    def __init__(self, job_id=None, client_ip=None):
        self.job_id = job_id
        self.client_ip = client_ip


