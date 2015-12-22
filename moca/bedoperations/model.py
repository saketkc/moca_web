#!/usr/bin/env python

import os
from ..helpers import exceptions
import pandas

column_names = ['chrom', 'chromStart', 'chromEnd', 'name', 'score', 'strand', 'signalValue', 'p-value', 'q-value']

class Bedfile(object):
    def __init__(filepath):
        self.filepath = filepath
        self.bed_format = None
        if not os.path.isfile(filepath):
            raise FileNotFoundError('Bed file {} not found'.format(filepath))

    def _guess_bed_format(self):
        bed_df = pandas.read_table(peak_file,header=None)


