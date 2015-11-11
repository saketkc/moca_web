
# coding: utf-8

# In[20]:

import requests
URL = 'https://www.encodeproject.org/search/?searchTerm=Chip-Seq&type=experiment&assembly=hg19&target.investigated_as=transcription%20factor&limit=all&format=json'
import sys
import time


# In[21]:

req = requests.get(URL)
result = req.json()
res = result['@graph']


# In[24]:

text=''
expts = []
for x in res:
    expt = x['@id'].rstrip('/').replace('/experiments/','')
    expts.append(expt)
    text+='{}\n'.format(expt)
#text+= res[-1]['@id'].rstrip('/').replace('/experiments/','')
#with open('encode_input.tsv','w') as f:
    #f.write(text)


# In[37]:

def check_status(job_id):
    status = 'pending'
    url = 'http://moca.usc.edu:5000'
    while status!='SUCCESS':
        req = requests.get('{}/status/{}'.format(url,job_id))
        resp = req.json()
        status = resp['status']
        if resp=='failure' or resp=='FAILURE':
            break
        time.sleep(1)
    return resp

__base_url__ = 'https://www.encodeproject.org/'

ALLOWED_OUTPUT_TYPES = ['optimal idr thresholded peaks', 'peaks']
ALLOWED_FILETYPES = ['bed narrowPeak', 'bed broadPeak']

def get_encode_peakfiles(encode_id):
    req = requests.get("{}experiments/{}/?format=json".format(__base_url__, encode_id))
    response_json = req.json()
    status = response_json['status']
    if status == 'error':
        return response_json
    files = response_json['files']
    biosample_term_name = response_json['biosample_term_name']
    assay_term_name = response_json['assay_term_name']
    description = response_json['description']
    gene_name = response_json['target']['label']
    files_to_download = []
    for f in files:
        file_type = f['file_type']
        file_status = f['status']
        if file_type in ALLOWED_FILETYPES:
            files_to_download.append(f['title'])
    return files_to_download

request_data = []
error_data = []

for ex in expts:
    files = get_encode_peakfiles(ex)
    for f in files:
        URL = 'http://moca.usc.edu:5000/encodejob/{}/{}'.format(ex, f)
        req = requests.post(URL)
        try:
            resp = req.json()['job_id']
            #check_status(resp)
            sys.stdout.write('{},{}\n'.format(ex,f))
        except Exception as e:
            sys.stderr.write('{},{}\n'.format(ex,f))
            sys.stderr.write('******Start*******\n')
            sys.stderr.write(req.content)
            sys.stderr.write('******End*********\n')
            sys.stderr.write('******Exception*******\n')
            sys.stderr.write(str(e))
            sys.stderr.write('******End*******\n')


# In[ ]:



