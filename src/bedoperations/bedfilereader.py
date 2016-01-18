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

