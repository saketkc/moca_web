#!/usr/bin/env python
"""
Script to analyse encode data
"""
from Bio import motifs
import glob
import logging
import sys
import os
import subprocess
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from random import seed
from random import randint
import shutil
import pandas
from config_processor import read_config
import json

binary_config = read_config('Binaries')
software_location = {}
software_location['calc_cons'] = binary_config['conservation_calculator']
software_location['plotter'] = binary_config['plotter']
software_location['meme'] = binary_config['meme']
software_location['fimo2sites'] = binary_config['fimo2sites']
software_location['fimo'] = binary_config['fimo']
software_location['extract_chunk'] = binary_config['extract_chunk']

error_messages= {k:'Error executing {}'.format(k) for k in software_location.keys()}

param_config = read_config('Parameters')

FLANKING_SEQ_LENGTH = int(param_config['flanking_seq_length'])
ENRICHMENT_SEQ_LENGTH = int(param_config['enrichment_seq_length'])
MOTIF_FLANKING_BASES = int(param_config['motif_flanking_bases'])
MAX_PEAKS_TO_KEEP = int(param_config['max_peaks_to_keep'])
N_MEME_MOTIFS = int(param_config['n_meme_motifs'])
FIMO_THRESHOLD = float(param_config['fimo_threshold'])

param_config = read_config('Parameters')

path_config = read_config('StaticPaths')
STATIC_PATH = path_config['job_render_path']
BASE_LOCATION = path_config['base_location']


FORMAT = '%(asctime)-15s %(message)s'
GENOME_TABLE =  ''#'/media/data1/genomes/hg19/fasta/hg19.sizes'
GENOME = ''# '/media/data1/genomes/hg19/fasta/hg19.fa'


class EncodeProcessor(object):

    def __init__(self, job_id, genome):
        self.path = os.path.join(BASE_LOCATION, job_id)
        self.genome = path_config[genome+'_genome']
        self.genome_table = path_config[genome+'_genome_table']
        self.destination_path = os.path.join(STATIC_PATH, job_id)
        self.total_motifs = None
        self.is_error = False
        self.error_log = None
        self.peak_file = os.path.join(self.path, 'peaks.tsv')
        ##TODO This should be general
        if not os.path.exists(self.destination_path):
            os.makedirs(self.destination_path)
        try:
           phylop_wig = path_config[genome+'_phylop_wig']
        except KeyError:
           phylop_wig = path_config[genome+'_phastcons_wig']
        try:
            gerp_wig = path_config[genome+'_gerp_wig']
        except KeyError:
            gerp_wig = ''
        self.phylop_wig = phylop_wig
        self.gerp_wig = gerp_wig
        log_file = os.path.join(self.path, 'run.log')
        logging.basicConfig(filename=log_file, level=logging.DEBUG, format=FORMAT, filemode='a')

    @staticmethod
    def dir_walker(path, level=2):
        s = '/*'*level
        file_depth = glob.glob('{}{}'.format(path, s))
        dirs = filter(lambda f: os.path.isdir(f), file_depth)
        return dirs
    @staticmethod
    def run_subprocess(command, cwd=None, stdout=subprocess.PIPE):
        print command
        split_command = command.split(' ')
        logging.info('*******Running command********')
        logging.debug('{}'.format(command))
        p = subprocess.Popen(split_command, cwd=cwd, stdout=stdout, stderr=subprocess.PIPE)
        output, stderr = p.communicate()
        returncode =p.returncode
        if (int(returncode)!=0):
            sys.stderr.write('Error executing: {}'.format(command))
            raise RuntimeError(command, output, stderr)
        logging.info('###########Output Start###########')
        logging.info(output)
        logging.info('###########Output End###########')
        return output

    @staticmethod
    def get_motifs(meme_file):
        handle = open(meme_file, 'r')
        records = motifs.parse(handle, 'meme')
        total_motifs = len(records)
        return total_motifs

    @staticmethod
    def generate_random_fasta(path, genome, genome_table):
        gt = None
        seed(1)
        with open(genome_table) as f:
            gt = f.readlines()
        chr_map = {}
        for line in gt:
            line = line.strip()
            s = line.split('\t')
            chr_map[s[0]] = int(s[1])
        records = list(SeqIO.parse(open(genome,'r'), 'fasta'))
        seqs = []
        chr_keys = chr_map.keys()
        for i in range(0,MAX_PEAKS_TO_KEEP):
            ## Avoid regions from scaffolds
            chr_idx = None
            chr_id = None
            while (chr_idx is None):
                chr_index = randint(0, len(chr_keys)-1)
                chr_id = chr_keys[chr_index]
                split = chr_id.split('_')
                if len(split)==1:
                    chr_idx = chr_id
                else:
                    pass
            record = None
            if chr_id is None:
                raise RuntimeError('Chr_id cannot be none')

            for r in records:
                if r.id == chr_id: #'chr{}'.format(chr_index):
                    record = r#records[chr_index]
            if not record:
                raise RuntimeError('No matching chrosome found for: {}'.format(chr_id))

            ##We use limit from genome_table!
            limit = chr_map[chr_id]
            start = randint(0, limit-FLANKING_SEQ_LENGTH-1)
            end = start+FLANKING_SEQ_LENGTH
            data = record.seq[start:end]
            seq = SeqRecord(data,'{}_{}_-{}'.format(chr_id, start, MOTIF_FLANKING_BASES),'','')
            seqs.append(seq)

        random_fasta = os.path.join(path,'random.fa')
        output_handle = open(random_fasta, 'w')
        logging.info('###########GeneratingRandomFA Start########################')
        SeqIO.write(seqs, output_handle, 'fasta')
        logging.info('###########GeneratingRandomFA End########################')
        output_handle.close()
        return random_fasta

    def motif_analysis(self):
        cwd = self.path
        sorted_write = open(os.path.join(cwd, 'peaks.sorted.tsv'), 'w')
        logging.info('############PeakSort Start########')
        self.run_subprocess("sort -k3,3nr -k1,1 peaks.tsv", cwd=cwd, stdout=sorted_write)
        logging.info('############PeakSort End########')
        head_write = open(os.path.join(cwd, 'peaks.sorted.top{}.tsv'.format(MAX_PEAKS_TO_KEEP)),'w')
        logging.info('############PeakHead Start########')
        self.run_subprocess("head -{} peaks.sorted.tsv".format(MAX_PEAKS_TO_KEEP), cwd=cwd, stdout=head_write)
        logging.info('############PeakHead End########')
        logging.info('############ExtractChunk Start########')
        try:
            self.run_subprocess("{0} positions_file=peaks.sorted.top{1}.tsv genome_table={2} genome_file={3} output_file=flanking_sequences_{4}.fa seq_length={4} offset={5}".format(software_location['extract_chunk'],
                                                                                                                                                                    MAX_PEAKS_TO_KEEP,
                                                                                                                                                                    self.genome_table,
                                                                                                                                                                    self.genome,
                                                                                                                                                                    FLANKING_SEQ_LENGTH, -FLANKING_SEQ_LENGTH/2),
                                cwd=cwd)
        except RuntimeError as e:
            raise RuntimeError(error_messages['extract_chunk'], e.args)
        logging.info('############ExtractChunk End########')
        logging.info('############ExtractChunkEmrichment Start########')
        try:
            self.run_subprocess("{0} positions_file=peaks.sorted.top{1}.tsv genome_table={2} genome_file={3} output_file=flanking_sequences_enrichment_{4}.fa seq_length={4} offset={5}".format(software_location['extract_chunk'],
                                                                                                                                                                                MAX_PEAKS_TO_KEEP,
                                                                                                                                                                                self.genome_table,
                                                                                                                                                                                self.genome,
                                                                                                                                                                                ENRICHMENT_SEQ_LENGTH, -ENRICHMENT_SEQ_LENGTH/2),
                            cwd=cwd)
        except RuntimeError as e:
            raise RuntimeError(error_messages['extract_chunk'], e.args)
        logging.info('############ExtractChunkEnrichment End########')
        logging.info('############MEMEAnalysis Start########')
        try:
            self.run_subprocess("{0} -p 24 -oc meme_analysis -dna -revcomp -nmotifs {1} -maxsize 1000000 flanking_sequences_{2}.fa".format(software_location['meme'], N_MEME_MOTIFS, FLANKING_SEQ_LENGTH), cwd=cwd)
        except RuntimeError as e:
            raise RuntimeError(error_messages['meme'], e.args)
        logging.info('############MEMEAnalysis End########')

    def conservation_analysis(self, motif):
        path = self.path
        peak_file = os.path.join(path, 'peaks.sorted.top{}.tsv'.format(MAX_PEAKS_TO_KEEP))
        print "Generate random fasta start"
        random_fasta = self.generate_random_fasta(path,self.genome, self.genome_table)
        print "Generate random fasta end"
        meme_file = os.path.join(path, 'meme_analysis', 'meme.txt')
        #meme_file_enrichment = os.path.join(path, 'meme_analysis_enrichment', 'meme.txt')
        fl = os.path.join(path, 'flanking_sequences_{}.fa'.format(FLANKING_SEQ_LENGTH))
        enrichment_sequence = os.path.join(path, 'flanking_sequences_enrichment_{}.fa'.format(ENRICHMENT_SEQ_LENGTH))
        fimo_path = os.path.join(path, 'fimo_analysis_with_flanking_motif_{}_{}_corrected'.format(motif, FIMO_THRESHOLD))
        fimo_path_enrichment = os.path.join(path, 'fimo_analysis_with_flanking_motif_enrichment_{}_{}_corrected'.format(motif, FIMO_THRESHOLD))
        fimo_path_random = os.path.join(path, 'fimo_analysis_with_flanking_motif_{}_{}_corrected_random'.format(motif, FIMO_THRESHOLD))
        fimo_in = os.path.join(fimo_path, 'fimo.txt')
        fimo_in_random = os.path.join(fimo_path_random, 'fimo.txt')
        fimo_in_enrichment = os.path.join(fimo_path_enrichment, 'fimo.txt')
        fimo_2_out = os.path.join(fimo_path, 'fimo_2_sites.txt')
        fimo_2_out_random = os.path.join(fimo_path_random, 'fimo_2_sites.txt')
        fimo_2_out_enrichment = os.path.join(fimo_path_enrichment, 'fimo_2_sites.txt')
        phylop_file = '100way_phyloP.flanking{}.txt'.format(MOTIF_FLANKING_BASES)
        gerp_file = 'RS_score.flanking{}.txt'.format(MOTIF_FLANKING_BASES)
        phyloP100way_out = os.path.join(fimo_path, phylop_file)
        gerp_out = os.path.join(fimo_path, gerp_file)
        phyloP100way_out_random = os.path.join(fimo_path_random, phylop_file)
        gerp_out_random = os.path.join(fimo_path_random, gerp_file)
        stats_phyloP100 = os.path.join(fimo_path, phylop_file+'.stats')
        stats_phyloP100_random = os.path.join(fimo_path_random, phylop_file+'.stats')
        stats_gerp = os.path.join(fimo_path, gerp_file + '.stats')
        stats_gerp_random = os.path.join(fimo_path_random, gerp_file + '.stats')

        ca_files = [(phyloP100way_out, phyloP100way_out_random), (gerp_out, gerp_out_random)]
        stats_files = [(stats_phyloP100, stats_phyloP100_random), (stats_gerp, stats_gerp_random)]

        logging.info('################Fimo Start##################')
        try:
            self.run_subprocess('{0} --motif {1} --thresh {2} -oc {3} {4} {5}'.format(software_location['fimo'], str(motif), float(FIMO_THRESHOLD), fimo_path, meme_file, fl), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo'], e.args)

        logging.info('################Fimo End##################')

        logging.info('################Fimo2Sites Start##################')
        try:
            self.run_subprocess('{0} fimo_file={1} output_file={2}'.format(software_location['fimo2sites'], fimo_in, fimo_2_out), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo2sites'], e.args)
        logging.info('################Fimo2Sites End##################')

        logging.info('################Fimo2Sites SortStart##################')
        p = pandas.read_table(fimo_2_out)
        c = p.sort(columns=['#chrom'])
        c.to_csv(fimo_2_out, sep='\t', index=False)
        logging.info('################Fimo2Sites SortEnd##################')

        logging.info('################FimoRandom Start##################')
        try:
            self.run_subprocess('{0} --motif {1} --thresh {2} -oc {3} {4} {5}'.format(software_location['fimo'], str(motif), float(FIMO_THRESHOLD), fimo_path_random, meme_file, random_fasta), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo'], e.args)
        logging.info('################FimoRandom End##################')

        logging.info('################Fimo2SitesRandom Start##################')
        try:
            self.run_subprocess('{0} fimo_file={1} output_file={2}'.format(software_location['fimo2sites'], fimo_in_random, fimo_2_out_random), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo2sites'], e.args)
        logging.info('################Fimo2SitesRandom End##################')
        p = pandas.read_table(fimo_2_out_random)
        c = p.sort(columns=['#chrom'])
        c.to_csv(fimo_2_out_random, sep='\t', index=False)

        logging.info('################FimoEnrichment Start##################')
        try:
            self.run_subprocess('{0} --motif {1} --thresh {2} -oc {3} {4} {5}'.format(software_location['fimo'], str(motif), float(FIMO_THRESHOLD), fimo_path_enrichment, meme_file, enrichment_sequence), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo'], e.args)

        logging.info('################FimoEnrichment End##################')

        logging.info('################Fimo2SitesEnrichment Start##################')
        try:
            self.run_subprocess('{0} fimo_file={1} output_file={2}'.format(software_location['fimo2sites'], fimo_in_enrichment, fimo_2_out_enrichment), cwd=path)
        except RuntimeError as e:
            raise RuntimeError(error_messages['fimo2sites'], e.args)
        logging.info('################Fimo2SitesEnrichment End##################')
        p = pandas.read_table(fimo_2_out_enrichment)
        c = p.sort(columns=['#chrom'])
        c.to_csv(fimo_2_out_enrichment, sep='\t', index=False)

        fimo_df = pandas.read_table(fimo_2_out)
        #fimo_df.columns =  fimo_2_site_columns

        fimo_en_df =  pandas.read_table(fimo_2_out_enrichment)
        #fimo_en_df.columns =  fimo_2_site_columns

        combined_fimo_df = pandas.merge(fimo_df, fimo_en_df, on=['#chrom', 'start', 'stop', 'strand'], how='outer')
        combined_fimo_df[['start', 'stop']] = combined_fimo_df[['start', 'stop']].astype(int)
        combined_fimo_df.to_csv(fimo_2_out_enrichment, sep='\t', index=False)

        for i, file_out in enumerate(ca_files):
            if i==0:
                phylo_in = self.phylop_wig
            if i==1:
                phylo_in = self.gerp_wig

            if phylo_in!='':
                logging.info('###########P100WaySiteConservationRandom Start########################')
                try:
                    self.run_subprocess('{} sample_sites_file={} control_sites_file={} sample_outfile={} control_outfile={} genome_table={} wig_file={} flank={}'.format(software_location['calc_cons'],
                                                                                                                                                                    fimo_2_out,
                                                                                                                                                                    fimo_2_out_random,
                                                                                                                                                                    file_out[0],
                                                                                                                                                                    file_out[1],
                                                                                                                                                                    self.genome_table,
                                                                                                                                                                    phylo_in,
                                                                                                                                                                    MOTIF_FLANKING_BASES))
                except RuntimeError as e:
                    raise RuntimeError(error_messages['calc_cons'], e.args)

                logging.info('###########P100WaySiteConservationRandom End########################')

        if self.gerp_wig!='':
            try:
                self.run_subprocess('{} -m {} -i {} -ps {} -pc {} -gs {} -gc {} -f {} -peak {} -fimo {}'.format(software_location['plotter'], motif,
                                                                                                        meme_file,
                                                                                                        stats_files[0][0],
                                                                                                        stats_files[0][1],
                                                                                                        stats_files[1][0],
                                                                                                        stats_files[1][1],
                                                                                                        MOTIF_FLANKING_BASES,
                                                                                                        peak_file,
                                                                                                        fimo_2_out_enrichment), cwd=self.destination_path)
            except RuntimeError as e:
                raise RuntimeError(error_messages['calc_cons'], e.args)
        else:
            try:
                self.run_subprocess('{} -m {} -i {} -ps {} -pc {} -f {} -peak {} -fimo {}'.format(software_location['plotter'],
                                                                                            motif,
                                                                                            meme_file,
                                                                                            stats_files[0][0],
                                                                                            stats_files[0][1],
                                                                                            MOTIF_FLANKING_BASES,
                                                                                            peak_file,
                                                                                            fimo_2_out_enrichment), cwd=self.destination_path)
            except RuntimeError as e:
                raise RuntimeError(error_messages['calc_cons'], e.args)

        static_destination = os.path.join(self.destination_path, 'motif{}'.format(motif))
        try:
            shutil.move(os.path.join(self.destination_path, 'motif{}Combined_plots.png'.format(motif)), static_destination + 'Combined_plots.png')
            shutil.move(os.path.join(self.destination_path, 'motif{}Combined_plots_rc.png'.format(motif)), static_destination + 'Combined_plots_rc.png')
        except:
            raise RuntimeError('Error moving files')


def get_summary(job_id, meme_file, peaks):
    """
    Write summary in a json file
    """
    summary = {}
    # Number of occurences in peak
    summary['motif_occurrences'] = {}
    # Number of peaks
    summary['original_peaks'] = peaks
    summary['peaks'] = min(MAX_PEAKS_TO_KEEP, peaks)
    records = motifs.parse(open(meme_file), 'meme')
    num_occurrences = []
    for index, record in enumerate(records):
        num_occurrences.append(int(getattr(record,'num_occurrences','Unknown')))

    sorted_occurences = sorted(enumerate(num_occurrences), key=lambda x: x[1])
    summary['motif_occurrences'] = {'motif{}'.format(index+1):value for index,value in sorted_occurences}
    fp = os.path.join(STATIC_PATH, job_id, 'summary.json')
    with open(fp, 'w') as f:
        json.dump(summary, f)
    print summary
    return summary


def run_motif_analysis(job_id, genome):
    encoder = EncodeProcessor(job_id, genome)
    analyse_motif = encoder.motif_analysis()
    with open(encoder.peak_file) as f:
        for i, line in enumerate(f):
            pass
    if analyse_motif:
        meme_file = os.path.join(encoder.path, 'meme_analysis', 'meme.txt')
        total_motifs = encoder.get_motifs(meme_file)
        encoder.total_motifs = total_motifs
        get_summary(job_id, meme_file, i+1)
        return encoder
    return False

def run_conservation_analysis(encoder_object, motif):
    encoder_object.conservation_analysis(motif)
    return True

def run_analysis(job_id, genome):
    encoder = EncodeProcessor(job_id, genome)
    analyse_motif = encoder.motif_analysis()
    with open(encoder.peak_file) as f:
        for i, line in enumerate(f):
            pass
    meme_file = os.path.join(encoder.path, 'meme_analysis', 'meme.txt')
    total_motifs = encoder.get_motifs(meme_file)
    encoder.total_motifs = total_motifs
    for motif in range(1,total_motifs+1):
        encoder.conservation_analysis(motif)
    summary = get_summary(job_id, meme_file, i+1)
    return summary
    #return False


if __name__ == '__main__':
    ## Full path to peak _file
    if (len(sys.argv)<2):
        sys.stderr.write("""Insufficient parameters. To Run: \n
                         python peaks_processor_celery.py <folder for peaks.tsv> <genome_name>""")
        sys.exit(1)

    job_id = sys.argv[1]
    genome = sys.argv[2]
    run_analysis(job_id, genome)
