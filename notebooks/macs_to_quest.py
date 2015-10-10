#!/usr/bin/env python
import pandas as pd
import os
import sys

def main(filename):
    df = pd.read_table(filename)
    if len(df.columns) != 5:
        sys.stderr.write('Error processing file: {}'.format(filename))
        sys.exit(1)
    df.columns = ['chrom', 'chromStart', 'chromEnd', 'name', 'value']
    df['peak'] = (df['chromStart']+df['chromEnd'])/2
    df['peak'] = df['peak'].astype(int)
    df1 = df[['chrom', 'peak', 'value']]
    df1 = df1.sort('value', ascending=False)
    outfile = os.path.splitext(filename)[0]
    outfile += ".quest"#".bed"
    df1.to_csv(outfile, sep='\t', index=False, header=False)

if __name__=='__main__':
    main(sys.argv[1])
