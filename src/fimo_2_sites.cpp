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
//#include "math_functions.h"
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


int main(int argc, char* argv[]){

  params pars(argc, argv);

  pars.require("fimo_file", "fimo_file", STRING_TYPE);
  pars.require("output_file", "output_file", STRING_TYPE);
  pars.optional("p_value_thresh", "p_value_thresh", "0.0001", DOUBLE_TYPE);
  pars.optional("track_name", "track_name", "motif_matches", STRING_TYPE);

  if(!pars.enforce()){
    exit(1);
  }

  string fimo_fname = pars.get_string_value("fimo_file");
  string output_fname = pars.get_string_value("output_file");
  
  double p_value_thresh = pars.get_double_value("p_value_thresh");
  string track_name = pars.get_string_value("track_name");

  string bed_output_fname = output_fname + ".bed";
  string dist_output_fname = output_fname + ".dist"; //record distances from the beginning of each sequence

  ofstream ofstr(output_fname.c_str());
  assert(ofstr.good());

  ofstream bed_ofstr(bed_output_fname.c_str());
  assert(bed_ofstr.good());

  ofstream dist_ofstr(dist_output_fname.c_str());
  assert(dist_ofstr.good());

  ifstream ifstr(fimo_fname.c_str());
  assert(ifstr.good());

  string for1 = "165,0,0";
  string for4 = "165,220,220";

  string rev1 = "0,165,0";
  string rev4 = "220,165,220";

  string line;
  
  char tab_char = '\t';
  char underscore_char = '_';
  
  ofstr<<"#chrom\tstart\tstop\tstrand\tp-value\tq-value"<<endl;
  bed_ofstr<<"track name=\""<<track_name<<"\" description=\""<<track_name<<"\" visibility=4 itemRgb=\"On\""<<endl;

  while(ifstr.good()){
    getline(ifstr, line);
    if(ifstr.good()){
      if(line.size() > 0){
	if(line[0] != '#'){
	  vector<string> line_fields = split(line, tab_char);
	  if(line_fields.size() >= 8){
	    //cout<<line_fields[1]<<endl;
	    int start = atoi(line_fields[2].c_str());
	    int stop = atoi(line_fields[3].c_str());
	    char strand = line_fields[4][0];
	    //double score = atof(line_fields[5].c_str());
	    double p_value = atof(line_fields[6].c_str());
	    double q_value = atof(line_fields[7].c_str());
	    string seq = line_fields[8];
	    
	    vector<string> coord_fields = split(line_fields[1], underscore_char);
	    if(coord_fields.size() == 3){
	      string chrom = coord_fields[0];
	      int region_start = atoi(coord_fields[1].c_str()) + atoi(coord_fields[2].c_str());
	      /*
	      int coord_start = atoi(coord_fields[1].c_str()) + atoi(coord_fields[2].c_str()) + start;
	      int coord_stop = atoi(coord_fields[1].c_str()) + atoi(coord_fields[2].c_str()) + stop + 1;
	      */
	      int offset = 0.5*(start+stop); //start; atoi(coord_fields[1].c_str());
	      //int coord_start = atoi(coord_fields[1].c_str()) + start;
	      //int coord_stop = atoi(coord_fields[1].c_str()) + stop + 1;

	      int coord_start = region_start + start;
	      int coord_stop = region_start + stop + 1;
						       
	      int bed_start = coord_start - 1;
	      int bed_stop = coord_stop -1;

	      bool report = false;
	      if(p_value <= p_value_thresh) report = true;

	      double minus_log_pvalue = -log(p_value)/log(10);
	      
	      if(report)
		ofstr<<chrom<<"\t"<<coord_start<<"\t"<<coord_stop<<"\t"<<strand<<"\t"<<p_value<<"\t"<<q_value<<endl;
	      
	      bed_ofstr<<chrom<<"\t"<<bed_start<<"\t"<<bed_stop<<"\t"<<(int)minus_log_pvalue<<"_"<<seq<<"\t1000"<<"\t"<<strand<<"\t"<<bed_start<<"\t"<<bed_stop;
	      dist_ofstr<<offset<<endl;
	      
	      if(strand == '+'){
		if(p_value <= p_value_thresh) bed_ofstr<<"\t"<<for1;
		else bed_ofstr<<"\t"<<for4;
	      }

	      if(strand == '-'){
		if(p_value <= p_value_thresh) bed_ofstr<<"\t"<<rev1;
		else bed_ofstr<<"\t"<<rev4;
	      }
	      bed_ofstr<<endl;
	      
	    } else {
	      cout<<"Warning. Field: "<<line_fields[1]<<endl;
	      cout<<"Expected 3 fields separatated by underscore, but found "<<coord_fields.size()<<endl;
	    }
	  } else {
	    cout<<"Warning. Not enough fields in line: "<<endl;
	    cout<<line<<endl;
	    cout<<"Skipping"<<endl<<endl;
	  }
	}
      }
    }
  }
  
  ifstr.close();
  ofstr.close();
  bed_ofstr.close();
  dist_ofstr.close();

  return 0;
}
