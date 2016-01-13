import subprocess
from .job_processor import JobProcessor

class MEMEJob(JobProcessor):
    """Runs meme command line

    Parameters
    ----------

    args: string
        String arguments as would be passed in command line

    Returns
    -------
    meme_job: object

    """
    def __init__(self):
        self.cmd = 'meme'

