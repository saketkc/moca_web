#!/usr/bin/env python
import pandas
import sys

column_names = ['chrom', 'chromStart', 'chromEnd', 'name', 'score', 'strand', 'signalValue', 'p-value', 'q-value']

def main(peak_file, genome_table):
    genome_table = pandas.read_table(genome_table, header=None, index_col=0)
    peak_df = pandas.read_table(peak_file,header=None)
    if len(peak_df.columns)==9:
        peak_df.columns = column_names
    elif len(peak_df.columns)==10:
        columns = column_names.append('peak')
        peak_df.columns = columns
    else:
        sys.stderr.write('Column length should be either 9 or 10, not: {}\n'.format(len(peak_df.columns)))
        sys.exit(1)
    for i, row in peak_df.iterrows():
        chrom = row['chrom']
        start = row['chromStart']
        end = row['chromEnd']
        limit = genome_table.ix[chrom][1]
        print start, limit
        if (start>limit) or (end>limit):
            sys.stderr.write('Cannot be greater: {} {} {} {}'.format(chrom, start, end, limit))
            sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv)<2:
        sys.stderr.write('Incorrect number of arguments. To Run:',
                         'python check_peakfile.py <peak_file> <genome_table>')
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
