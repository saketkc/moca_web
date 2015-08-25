#include <iostream>
#include <math.h>
#include <fstream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <exception>
#include <stdio.h>
#include <assert.h>

#include "params.h"
#include "genome.h"
#include "string_utils.h"
#include "genome_table.h"
#include "math_functions.h"
#include "sequence_utility_functions.h"
//#include "paths.h"

using std::ifstream;
using std::ofstream;

using std::istringstream;
using std::cerr;
using std::endl;
using std::cout;

struct genome_coord{
  string chrom;
  int pos;
};

//extract a given sequence window at a given distance away from the site
//this can be used to search motifs with MEME

int main(int argc, char* argv[]){

  params pars(argc, argv);

  pars.require("positions_file", "positions_file", STRING_TYPE);
  pars.require("genome_table", "genome_table", STRING_TYPE);
  //pars.require("analysis_path", "analysis_path", STRING_TYPE);
  pars.require("genome_file", "genome_file", STRING_TYPE);
  pars.require("output_file", "output_file", STRING_TYPE);
  pars.optional("seq_length", "seq_length", "20", INT_TYPE);
  pars.optional("offset", "offset", "-10", INT_TYPE);


  if(!pars.enforce()){
    exit(1);
  }

  string gt_fname = pars.get_string_value("genome_table");
  //string analysis_path = pars.get_string_value("analysis_path");
  string genome_fname = pars.get_string_value("genome_file");
  string positions_fname = pars.get_string_value("positions_file");
  int seq_length = pars.get_int_value("seq_length");
  int offset = pars.get_int_value("offset");

  cout<<"offset: "<<offset<<endl;

  string output_fname = pars.get_string_value("output_file");
  ofstream ofstr(output_fname.c_str());

  //if(analysis_path[analysis_path.size()-1]!='/')
  //  analysis_path = analysis_path + "/";

  genome g(genome_fname);

  //string gt_fname = analysis_path + genome_table_suffix;
  genome_table gt(gt_fname);

  ifstream positions_ifstr(positions_fname.c_str());
  assert(positions_ifstr.good());

  string line;
  vector<genome_coord> sites;
  char tab_char = '\t';

  while(positions_ifstr.good()){
    getline(positions_ifstr, line);
    if(positions_ifstr.good()){
      vector<string> line_fields = split(line, tab_char);
      if(line_fields.size() >= 2){
        genome_coord cur_site;
        cur_site.chrom = line_fields[0];
        cur_site.pos = atoi(line_fields[1].c_str());
        sites.push_back(cur_site);
      }
    }
  }
  positions_ifstr.close();

  cout<<"read "<<sites.size()<<endl;


  for(unsigned int k=0; k<gt.size(); k++){
    string cur_chrom = gt.contigs[k];
    //int cur_chrom_size = gt.contig_sizes[k];

    for(unsigned int i=0; i<sites.size(); i++){
      if(sites[i].chrom == cur_chrom){
        int cur_pos = sites[i].pos;

        string cur_seq = g.get_seq(cur_chrom, cur_pos + offset, seq_length, false);
        cur_seq = capitalize(cur_seq);
        ofstr<<">"<<cur_chrom<<"_"<<cur_pos<<"_"<<offset<<endl;
        ofstr<<cur_seq<<endl;
      }
    }
  }

  ofstr.close();

  return 0;
}
