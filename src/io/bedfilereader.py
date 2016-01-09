import os
from ..helpers import MocaException
import pandas

__BED_COLUMNS__ = ['chrom', 'chromStart', 'chromEnd',
                   'name', 'score', 'strand',
                   'signalValue', 'p-value', 'q-value']

__BED_TYPES__ = {10: 'narrowPeak',
                 9: 'broadPeak',
                 3: 'questPeak'}

class Bedfile(object):
    """Main class to read bedfiles

    Main class used to read bed files and stores
    them as pandas dataframes.

    Example:
        >>> from moca.io import Bedfile
        >>> bf = Bedfile('chr1.bed')
        >>> print(bf.columns[0])
        ['chrom']
    To sort,
        >>> bf.sort()
    """

    def __init__(self, filepath, header=True):
        """Constructor class for Bedfile.

        Parameters
        ----------
        filepath: string
            Absolute path to bed file
        header: bool
            Whether header line from bed file should be used

        Returns
        -------
        bed_df: dataframe
            Pandas dataframe containing

        """
        self.filepath = filepath
        self.columns = None
        self.bedformat = None
        self.bed_df = None
        if not os.path.isfile(filepath):
            raise MocaException('Bed file {} not found'.format(self.filepath))
        self._read()
        self.bedformat = self.guess_bedformat()

    def _read(self):
        try:
            self.bed_df = pandas.read_table(self.filepath,
                                        header=None)
        except Exception as e:
            raise MocaException('Error reading bed file {}'.format(self.filepath),
                                'Traceback: {}'.format(e))

    def guess_bedformat(self):
        """Method to guess bed format
        Returns
        -------
        bed_format: string
            BED format

        Example:
            >>> bed_df = Bedfile('file.bed')
            >>> print(bed_df.guess_bed_format())

        """
        self.bed_columns = self.bed_df.columns
        count = len(self.bed_columns)
        try:
            bed_format = __BED_TYPES__[count]
        except KeyError:
            raise MocaException('Bed file had {} columns. Supported column lengths are {}')
        return bed_format

    def sort_by(self, columns=None, ascending=False):
        """Method to sort columns of bedfiles
        Parameters
        ----------
        columns: list
            list of column names to sort by
        ascending: bool
            Sort order(Default: true)

        Returns
        -------
        sorted_bed_df: dataframe
            dataframe with sorted columns
        """
        assert type(columns) is list
        return self.bed_df.sort(columns, ascending)
