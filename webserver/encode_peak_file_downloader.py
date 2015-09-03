#!/usr/bin/env python

import requests
import sys

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
        if file_type in ALLOWED_FILETYPES:
            dataset = f['dataset']
            dataset = dataset.replace('experiments','').replace('/','')
            assert (dataset == encode_id)
            assembly = f['assembly']
            #href = __base_url__ + f['href']
            href = f['href']
            output_type = f['output_type']
            #assert output_type in ALLOWED_OUTPUT_TYPES
            #print f.keys()#['replicate']#['technical_replicate_number']
            try:
               tech_repl_number =  f['replicate']['technical_replicate_number']
               bio_repl_number = f['replicate']['biological_replicate_number']
            except KeyError:
                assert (output_type in ALLOWED_OUTPUT_TYPES)
                tech_repl_number =  ''
                bio_repl_number = ''

            files_to_download.append({'href': href, 'tech_repl_number': tech_repl_number,
                                      'bio_repl_number': bio_repl_number,
                                      'output_type': output_type.replace('bed ',''),
                                      'file_type': file_type,
                                      'title': f['title'],
                                      'dataset':dataset,
                                      'assembly': assembly,
                                      'biosample_term_name': biosample_term_name,
                                      'assay_term_name': assay_term_name,
                                      'gene_name': gene_name,
                                      'description': description})
    return files_to_download

def get_metadata_for_peakfile(dataset, peakfile):
    #TODO this is repeated from last function and probaly is an inefficient way to implement this
    req = requests.get("{}experiments/{}/?format=json".format(__base_url__, dataset))
    response_json = req.json()
    status = response_json['status']
    files = response_json['files']
    biosample_term_name = response_json['biosample_term_name']
    assay_term_name = response_json['assay_term_name']
    description = response_json['description']
    gene_name = response_json['target']['label']
    if status == 'error':
        return response_json
    for f in files:
        title = f['title']
        if title == peakfile:
            assembly = f['assembly']
            href = __base_url__ + f['href']
            output_type = f['output_type']
            try:
               tech_repl_number =  f['replicate']['technical_replicate_number']
               bio_repl_number = f['replicate']['biological_replicate_number']
            except KeyError:
                assert (output_type in ALLOWED_OUTPUT_TYPES)
                tech_repl_number =  ''
                bio_repl_number = ''
            return {'href': href,
                    'tech_repl_number': tech_repl_number,
                    'bio_repl_number': bio_repl_number,
                    'output_type': output_type,
                    'title': f['title'],
                    'file_type': f['file_type'].replace('bed ',''),
                    'dataset':dataset,
                    'assembly': assembly,
                    'biosample_term_name': biosample_term_name,
                    'assay_term_name': assay_term_name,
                    'gene_name': gene_name,
                    'description': description
                    }

    return None

if __name__=='__main__':
    if len(sys.argv)<2:
        print ('Usage: python encode_peak_file_downloader.py <encode_id>')
        sys.exit(1)

    print get_encode_peakfiles(sys.argv[1])
