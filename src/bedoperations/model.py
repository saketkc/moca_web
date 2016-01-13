#!/usr/bin/env python

import os
from ..helpers import exceptions
import pandas
from pybedtools import BedTool


column_names = ['chrom', 'chromStart', 'chromEnd', 'name', 'score', 'strand', 'signalValue', 'p-value', 'q-value']

class Bedfile(object):
    """Class to crate a bed file object
    Parameters
    ----------
    filepath: string
        Absolute path to bedfile

    genome_table: string
        Absolute path to geonme chromosome size file
    """
    def __init__(self, filepath, genome_table):
        self.filepath = filepath
        self.bed_format = None
        if not os.path.isfile(filepath):
            raise FileNotFoundError('Bed file {} not found'.format(filepath))
        self.bed_format = self._guess_bed_format()
        self.bed_sort()
        self.bed = Bedtool(filepath)
        self.genome_table = genome_table
        assert self.bed_Format is not None

    def bed_sort(self):
        self.bed_df.sort(columns=['scopre'], ascending=False)
        filename, file_extension = os.path.splitext(self.filepath)
        filename += '.sorted'
        self.sorted_bed = filename+file_extension
        self.bed_df.to_csv(filename+file_extension,
                           sep='\t',
                           columns=['chrom', 'peak_positions', 'score'],
                           index=False,
                           header=False)


    def _guess_bed_format(self):
        self.bed_df = pandas.read_table(self.filepath,
                                   header=None)
        self.bed_columns = self.bed_df.columns
        cols = len(self.bed_columns)
        if cols==10:
            return 'narrowPeak'
        elif cols==9:
            return 'broadPeak'
        elif cols==3:
            return 'questPeak'
        return 'unknown'


    def bed_slop(self, flank_length=5):
        """Add flanking sequences to bed file
        Parameters
        ----------
        flank_length: int
            the bed region is expanded in both direction by flank_length number of bases
        Returns
        -------
        slop_bed: dataframe
            Slopped bed data object
        """
        self.bed.slop(g=self.genome_table,
                      b=flank_length
                      )
    def extract_fasta(self, fasta_file):
        """Extract fasta of bed regions
        Parameters
        ----------
        fasta_file: string
            Absolute path to location of fasta file
        Returns
        -------
        fasta: string
            Fasta sequence combined
        """
        self.bed.sequence(fi=fasta_file)
