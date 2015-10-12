
# coding: utf-8

# In[17]:

import requests
import os
import ntpath
import pandas as pd
from time import sleep


# In[18]:

URL = 'http://moca.usc.edu'
data = {'genome': 'hg19', 'format':'json'}
request_data = []
error_data = []
files_to_process = []


# In[19]:

for file in os.listdir("/home/saket/Desktop/chip_scoring_beds/"):
    if file.endswith(".quest"):
        filename = "/home/saket/Desktop/chip_scoring_beds/{}".format(file)
        fn = ntpath.basename(filename)
        files_to_process.append(filename)
def check_status(job_id):
    status = 'pending'
    while status!='SUCCESS':
        req = requests.get('{}/status/{}'.format(URL,job_id))
        resp = req.json()
        status = resp['status']
        if resp=='failure' or resp=='FAILURE':
            break
    return resp


# In[16]:

for filename in files_to_process:
        files = {'file': open(filename, 'rb')}
        req = requests.post(URL, files=files, data=data)
        try:
            resp = req.json()['job_id']
            check_status(resp)
            request_data.append((fn, resp))
        except:
            print 'Failed: {}'.format(filename)
            print req.content
            error_data.append((fn))


# In[17]:

rurl = 'http://moca.usc.edu:5000/results/'
df = pd.DataFrame(columns = ('filename', 'link'))
for x, d in enumerate(request_data):
    df.loc[x] = [d[0], rurl+d[1]]
df.to_csv('encode_results.tsv', index=False, sep='\t')

