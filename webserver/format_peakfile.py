#!/usr/bin/env python
import pandas
import sys
import os

column_names = ['chrom', 'chromStart', 'chromEnd', 'name', 'score', 'strand', 'signalValue', 'p-value', 'q-value']

def convert_to_scorefile(filepath, filetype):
    assert filetype in ['broadPeak', 'narrowPeak']
    df = pandas.read_table(filepath, header=None)
    ## if file is narrow peak, the speak summit occurs
    #3 at 0-based offset given in the last columi
    if filetype=='broadPeak':
        df.columns = column_names
    else:
        columns = column_names[:]
        columns.append('peak')
        df.columns = columns

    if filetype=='narrowPeak':
        df['peak_positions'] = df['chromStart']+df['peak']
    else:
        df['peak_positions'] = (df['chromStart']+df['chromEnd'])
        df['peak_positions'] = [int(x/2) for x in df['peak_positions']]

    out_file = os.path.join(os.path.dirname(filepath), 'peaks.tsv')
    df = df.sort(columns=['score'], ascending=False)
    df.to_csv(out_file, sep='\t', columns=['chrom', 'peak_positions', 'score'], index=False, header=False)

if __name__ == '__main__':
    convert_to_scorefile(sys.argv[1], sys.argv[2])

