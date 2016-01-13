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
from pathos.multiprocessing import ProcessingPool
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from random import randint



__base_location__ = '/panfs/cmb-panasas2/skchoudh/encode_data/'
__phyloP100way__ = '/panfs/cmb-panasas2/skchoudh/genomes/HSapiens/hg19/hg19.100way.phyloP100way.wig'
__phyloP46way__ = '/panfs/cmb-panasas2/skchoudh/genomes/HSapiens/hg19/hg19.46way.phyloP46way.wig'
__gerp__ = '/panfs/cmb-panasas2/skchoudh/genomes/HSapiens/hg19/All_hg19_RS.wig'
__phastCons100way__ = '/panfs/cmb-panasas2/skchoudh/genomes/HSapiens/hg19/hg19.100way.phastCons.wig'
__phastCons20way__ = '/panfs/cmb-panasas2/skchoudh/genomes/HSapiens/hg19/hg19.20way.phastCons.wig'
__genome_table__ = '/home/rcf-40/skchoudh/genome/hg19.sizes'
__genome__ = '/home/rcf-40/skchoudh/genome/hg19.fa'
meme_processor = '/panfs/cmb-panasas2/skchoudh/binaries/meme_processor_multiplex.py'
quest_location = '/panfs/cmb-panasas2/skchoudh/software_frozen/brew/linuxbrew/Cellar/quest/2.4/bin/generate_QuEST_parameters_noninteractive_update.pl'
__thresh__ = 0.0001

def dir_walker(path, level=2):
    s = '/*'*level
    file_depth = glob.glob('{}{}'.format(path, s))
    dirs = filter(lambda f: os.path.isdir(f), file_depth)
    return dirs

def run_subprocess(command, cwd=None, stdout=None):
    split_command = command.split(' ')
    logging.info('*******Running command********')
    logging.debug('{}'.format(command))
    output = subprocess.call(split_command, cwd=cwd, stdout=stdout)
    logging.info('###########Output Start###########')
    logging.info(output)
    logging.info('###########Output End###########')
    return output

def get_motifs(meme_file):
    handle = open(meme_file, 'r')
    records = motifs.parse(handle, 'meme')
    total_motifs = len(records)
    return total_motifs


def generate_random_fasta(path):
    gt = None
    with open(__genome_table__) as f:
        gt = f.readlines()
    chr_map = {}
    for line in gt:
        line = line.strip()
        s = line.split('\t')
        chr_map[s[0]] = int(s[1])
    records = list(SeqIO.parse(open(__genome__,'r'), 'fasta'))
    seqs = []

    for i in range(0,1000):
        chr_index = randint(1, 22)
        chr_id = None
        for r in records:
            if r.id == 'chr{}'.format(chr_index):
                record = records[chr_index]
                chr_id = r.id
        ##We use limit from genome_table!
        ##I think it ignores N
        limit = chr_map[chr_id]
        start = randint(0, limit-200)
        end = start+200
        data = record.seq[start:end]
        seq = SeqRecord(data,'{}_{}_-10'.format(chr_id, start),'','')
        seqs.append(seq)

    random_fasta = os.path.join(path,'random.fa')
    output_handle = open(random_fasta, 'w')
    logging.info('###########GeneratingRandomFA Start########################')
    SeqIO.write(seqs, output_handle, 'fasta')
    logging.info('###########GeneratingRandomFA End########################')
    output_handle.close()
    return random_fasta

def conservation_analysis(data):
    path = data['path']
    random_fasta = data['random_fasta']
    motif = data['motif']
    path = os.path.join(path, 'quest_output_withIP', 'conservation_analysis')
    meme_file = os.path.join(path, 'meme_analysis', 'meme.txt')
    fl = os.path.join(path, 'flanking_sequences_200.fa')
    #for motif in range(1, total_motifs+1):
    fimo_path = os.path.join(path, 'fimo_analysis_with_flanking_motif_{}_{}_corrected'.format(motif, __thresh__))
    fimo_path_random = os.path.join(path, 'fimo_analysis_with_flanking_motif_{}_{}_corrected_random'.format(motif, __thresh__))
    fimo_in = os.path.join(fimo_path, 'fimo.txt')
    fimo_in_random = os.path.join(fimo_path_random, 'fimo.txt')
    fimo_2_out = os.path.join(fimo_path, 'fimo_2_sites.txt')
    fimo_2_out_random = os.path.join(fimo_path_random, 'fimo_2_sites.txt')
    phyloP100way_out = os.path.join(fimo_path, '100way_phyloP.flanking10.txt')
    phyloP46way_out = os.path.join(fimo_path, '46way_phyloP.flanking10.txt')
    phastCons100way_out = os.path.join(fimo_path, '100way_phastCons.flanking10.txt')
    gerp_out = os.path.join(fimo_path, 'RS_score.flanking10.txt')
    phyloP100way_out_random = os.path.join(fimo_path_random, '100way_phyloP.flanking10.txt')
    phyloP46way_out_random = os.path.join(fimo_path_random, '46way_phyloP.flanking10.txt')
    phastCons100way_out_random = os.path.join(fimo_path_random, '100way_phastCons.flanking10.txt')
    gerp_out_random = os.path.join(fimo_path_random, 'RS_score.flanking10.txt')
    stats_phyloP100 = os.path.join(fimo_path, '100way_phyloP.flanking10.txt.stats')
    stats_phyloP100_random = os.path.join(fimo_path_random, '100way_phyloP.flanking10.txt.stats')
    stats_phyloP46 = os.path.join(fimo_path, '46way_phyloP.flanking10.txt.stats')
    stats_phyloP46_random = os.path.join(fimo_path_random, '46way_phyloP.flanking10.txt.stats')
    stats_phastCons100 = os.path.join(fimo_path, '100way_phastCons.flanking10.txt.stats')
    stats_phastCons100_random = os.path.join(fimo_path_random, '100way_phastCons.flanking10.txt.stats')
    stats_gerp = os.path.join(fimo_path, 'RS_score.flanking10.txt.stats')
    stats_gerp_random = os.path.join(fimo_path_random, 'RS_score.flanking10.txt.stats')

    ca_files = [(phyloP100way_out, phyloP100way_out_random),(phyloP46way_out, phyloP46way_out_random),(phastCons100way_out, phastCons100way_out_random), (gerp_out, gerp_out_random)]
    stats_files = [(stats_phyloP100, stats_phyloP100_random),(stats_phyloP46, stats_phyloP46_random),(stats_phastCons100, stats_phastCons100_random), (stats_gerp, stats_gerp_random)]

    #phastCons20way_out = os.path.join(fimo_path, '20way_phastCons_site_conservation.flanking10.txt')
    logging.info('################Fimo Start##################')
    run_subprocess('fimo --motif {0} --thresh {1} -oc {2} {3} {4}'.format(str(motif), float(__thresh__), fimo_path, meme_file, fl), cwd=path)
    logging.info('################Fimo End##################')

    logging.info('################Fimo2Sites Start##################')
    run_subprocess('fimo_2_sites fimo_file={} output_file={}'.format(fimo_in, fimo_2_out), cwd=path)
    logging.info('################Fimo2Sites End##################')

    logging.info('################FimoRandom Start##################')
    run_subprocess('fimo --motif {0} --thresh {1} -oc {2} {3} {4}'.format(str(motif), float(__thresh__), fimo_path_random, meme_file, random_fasta), cwd=path)
    logging.info('################FimoRandom End##################')

    logging.info('################Fimo2SitesRandom Start##################')
    run_subprocess('fimo_2_sites fimo_file={} output_file={}'.format(fimo_in_random, fimo_2_out_random), cwd=path)
    logging.info('################Fimo2SitesRandom End##################')

    for i, file_out in enumerate(ca_files):
        if i==0:
            phylo_in = __phyloP100way__
        if i==1:
            phylo_in = __phyloP46way__
        if i==2:
            phylo_in = __phastCons100way__
        if i==3:
            phylo_in = __gerp__

        logging.info('###########P100WaySiteConservation Start########################')
        run_subprocess('calculate_site_conservation_read_binary sites_file={} genome_table={} wig_file={} output_file={} flank=10'.format(fimo_2_out, __genome_table__ ,phylo_in, file_out[0]))
        logging.info('###########P100WaySiteConservation End########################')

        logging.info('###########P100WaySiteConservationRandom Start########################')
        run_subprocess('calculate_site_conservation_read_binary sites_file={} genome_table={} wig_file={} output_file={} flank=10'.format(fimo_2_out_random, __genome_table__ ,phylo_in, file_out[1]))
        logging.info('###########P100WaySiteConservationRandom End########################')

    for stat_file in stats_files:
        logging.info('###########Plotter Start########################')
        run_subprocess('meme_processor_with_controls.py -m {0} -i {1} -cs {2} -cc {3} -f 10'.format(motif, meme_file, stat_file[0], stat_file[1]))
        logging.info('###########Plotter End########################')

    run_subprocess('plotter.py -m {0} -i {1} -ps {2} -pc {3} -gs {4} -gc {5} -f 10'.format(motif, meme_file, stats_files[0][0], stats_files[0][1], stats_files[3][0], stats_files[3][1]), cwd=path)

class EncodeProcessor(object):
    def __init__(self, encode_root):
        self.encode_root = os.path.join(__base_location__, encode_root)
        self.control_bam = None
        self.reference_chrs = '/auto/rcf-40/skchoudh/genome/chromosomes/'

    def run_subprocess(self, command, cwd=None, stdout=None):
        split_command = command.split(' ')
        logging.debug('*******Running command********')
        logging.debug('{}'.format(command))
        output = subprocess.call(split_command, cwd=cwd, stdout=stdout)
        logging.info('###########Output Start###########')
        logging.info(output)
        logging.info('###########Output End###########')
        return output

    def bam_to_sam(self, bam_path):
        sam_path = bam_path[:-3]+'sam'
        cwd = os.path.dirname(bam_path)
        logging.info('############BamtoSam Start########')
        self.run_subprocess("samtools view -h -o {0} {1}".format(sam_path, bam_path), cwd=cwd)
        logging.info('############BamtoSam End########')
        return sam_path

    def control_analysis(self, bam_dir):
        files = os.listdir(bam_dir)
        control_bam = None
        for f in files:
            if '.bam' in f:
                control_bam = os.path.join(bam_dir, f)
        assert control_bam is not None
        control_sam = self.bam_to_sam(control_bam)
        logging.info('############QuESTControl Start########')
        self.run_subprocess('{} -sam_align_ChIP {} -rp {} -ap quest_output_control -silent'.format(quest_location, control_sam, self.reference_chrs), cwd=bam_dir)
        logging.info('############QuESTControl End########')

    def sample_analysis(self, sample_dir):
        cwd = sample_dir
        for f in os.listdir(sample_dir):
            if '.bam' in f:
                sample_bam = os.path.join(sample_dir, f)
        logging.info('############QuESTSample Start########')
        control_sam = self.control_sam
        sample_sam = self.bam_to_sam(sample_bam)
        cwd = os.path.dirname(sample_sam)
        self.run_subprocess('{} -sam_align_ChIP {} -sam_align_RX_noIP {} -rp {} -ap quest_output_withIP -silent'.format(quest_location, sample_sam, control_sam, self.reference_chrs),
                            cwd=cwd)
        logging.info('############QuESTSample End########')

    def run_all_control_analysis(self):
        dirs = dir_walker(self.encode_root)
        control_dir = None
        for d in dirs:
            if 'control' in d.lower():
                control_dir = d
        assert control_dir is not None
        replicates = dir_walker(control_dir, level=1)
        pool = ProcessingPool(nodes=14)
        pool.map(self.control_analysis, tuple(replicates))
        return replicates

    def control_with_max_peaks(self, control_dirs):
        ## We simply select the control with max peaks rather than
        ## doing some kind of intersectio/union
        ## Ideally the peaks should be combined for all controls
        ## and the intersection should be over replicates
        max_peaks = 0
        max_peak_control = None
        control_sam = None
        for control in control_dirs:
            with open(os.path.join(control,  'quest_output_control', 'module_outputs', 'QuEST.out')) as f:
                lines = f.readlines()
            count = float(lines[7].strip().split(': ')[1])
            if count > max_peaks:
                max_peaks = count
                max_peak_control = control
        for f in os.listdir(max_peak_control):
            if '.sam' in f:
                control_sam = os.path.join(max_peak_control, f)
        assert control_sam is not None
        logging.info('*******Control with max peaks********: {} \n and\n ***max peak***s: {}\n'.format(max_peak_control, max_peaks))
        return control_sam

    def get_all_samples(self):
        dirs = os.listdir(self.encode_root)
        technical_replicates = []
        bio_replicates = []
        for d in dirs:
            if 'Control' not in d:
                technical_replicates.append(d)
        for tr in technical_replicates:
            dirs = os.listdir(os.path.join(self.encode_root,tr))
            for d in dirs:
                    if 'bio' in d:
                        bio_replicates.append(os.path.join(self.encode_root,tr,d))
        return bio_replicates

    def analyse_samples_parallely(self, samples_dirs):
        pool = ProcessingPool(nodes=15)
        pool.map(self.sample_analysis, tuple(samples_dirs))

    def search_peaks(self, cwd_ca):
        peaks = os.path.join(cwd_ca, 'calls', 'peak_caller.ChIP.out.accepted')
        peaks_out = os.path.join(cwd_ca, 'conservation_analysis', 'peaks.tsv')
        with open(peaks) as f:
            data = f.readlines()
        peak_lines = []
        for line in data:
            line = line.strip()
            if 'P-' in line:
                peak_lines.append(line)
        w = ''
        for line in peak_lines:
            s = line.split(' ')
            w += '{}\t{}\t{}\n'.format(s[1], s[2], s[4])
        #w=w[:-1]
        with open(peaks_out, 'w') as f:
            f.write(w)
        return os.path.dirname(peaks_out)

    def sample_motif_analysis(self, sample_dir):
        cwd = os.path.join(sample_dir, 'quest_output_withIP')
        cwd_ca = os.path.join(cwd, 'conservation_analysis')
        if not os.path.exists(cwd_ca):
            os.mkdir(cwd_ca)
        #cat = self.run_subprocess("cat calls/peak_caller.ChIP.out.accepted", cwd=cwd)
        #grep = self.run_subprocess("grep 'P-'", cwd = cwd, stdin=cat)
        #awk = self.run_subprocess("awk '{print $2\"\t\"$9\"\t\"$5}' > conservation_analysis/peaks.tsv", cwd=cwd, stdin=grep)
        self.search_peaks(cwd)
        sorted_write = open(os.path.join(cwd_ca, 'peaks.sorted.tsv'), 'w')
        logging.info('############PeakSort Start########')
        self.run_subprocess("sort -k3,3nr -k1,1 peaks.tsv", cwd=cwd_ca, stdout=sorted_write)
        logging.info('############PeakSort End########')
        head_write = open(os.path.join(cwd_ca, 'peaks.sorted.top500.tsv'),'w')
        logging.info('############PeakHead Start########')
        self.run_subprocess("head -500 peaks.sorted.tsv", cwd=cwd_ca, stdout=head_write)
        logging.info('############PeakHead End########')
        logging.info('############ExtractChunk Start########')
        self.run_subprocess("extract_sequence_chunks_near_sites positions_file=peaks.sorted.top500.tsv genome_table=/auto/rcf-40/skchoudh/genome/hg19.sizes genome_file=/auto/rcf-40/skchoudh/genome/hg19.fa output_file=flanking_sequences_200.fa seq_length=200",
                            cwd=cwd_ca)
        logging.info('############ExtractChunk End########')
        logging.info('############MEMEAnalysis Start########')
        self.run_subprocess("meme -oc meme_analysis -dna -revcomp -nmotifs 3 -maxsize 1000000 flanking_sequences_200.fa", cwd=cwd_ca)
        logging.info('############MEMEAnalysis End########')

    def parallel_motif_analysis(self, samples_dirs):
        pool = ProcessingPool(nodes=16)
        pool.map(self.sample_motif_analysis, tuple(samples_dirs))


if __name__ == '__main__':
    encode_id = sys.argv[1]
    encoder = EncodeProcessor(encode_id)
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename='/panfs/cmb-panasas2/skchoudh/encode_data/jobs/logs/{}-extended-plots.debug'.format(encode_id),level=logging.DEBUG, format=FORMAT, filemode='a')
    samples = encoder.get_all_samples()
    #control_dirs = encoder.run_all_control_analysis()
    #max_control_peak = encoder.control_with_max_peaks(control_dirs)
    #encoder.control_sam = max_control_peak
    #analyse_samples = encoder.analyse_samples_parallely(samples)
    for i, sample in enumerate(samples):
        path = os.path.join(sample, 'quest_output_withIP', 'conservation_analysis')
        #encoder.sample_motif_analysis(sample)
        random_fasta = os.path.join(path, 'random.fa')#generate_random_fasta(path)
        meme_file = os.path.join(path, 'meme_analysis', 'meme.txt')
        total_motifs = get_motifs(meme_file)
        for motif in range(1, total_motifs+1):
            data = {}
            data['path'] = sample
            data['motif'] = motif
            data['random_fasta'] = random_fasta
            conservation_analysis(data)

