#include <iostream>
#include <math.h>
#include <fstream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <exception>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>

#include "params.h"
#include "string_utils.h"
#include "genome_table.h"
#include "math_functions.h"

using std::ifstream;
using std::ofstream;

using std::istringstream;
using std::cerr;
using std::endl;
using std::cout;

struct genome_coord{
  string chrom;
  int pos;
  char strand;
  double value;
};

struct genome_region{
  string chrom;
  int start;
  int end;
  char strand;
  double p_value;
  double q_value;
};


bool pos_less(const genome_coord& l, const genome_coord& r){
  return l.pos < r.pos;
}

void write_wig_binary(string& wig_name,  string chr_name, vector<float> &wig){
    string binary_path;
    binary_path = wig_name +  "__" + chr_name + ".wigbin";
    ofstream wig_binary (binary_path.c_str(), ofstream::binary);
    const char* buffer = reinterpret_cast<const char*>(&wig[0]);
    wig_binary.write(buffer, wig.size()*sizeof(float));
    wig_binary.close();
}

void check_missing_wigs(string& wig_name, genome_table& gt){
    string binary_path;
    string cur_chrom;
    vector<float> wig;
    for(unsigned int i=0; i<gt.contig_sizes.size(); i++){
        string cur_chrom = gt.contigs[i];
        binary_path = wig_name +  "__" + cur_chrom + ".wigbin";
        ifstream f(binary_path.c_str());
        if (!f.good()){
            //File does not exist. Create one with all entries initialised to 0
            cout<<"WARNING: Creating empty wigbin for: "<<gt.contigs[i]<<endl;
            int cur_contig_ind = gt.contig_ind(cur_chrom); //contig_sizes[contig_ind];
            int cur_chrom_size = gt.contig_sizes[cur_contig_ind];
            wig.resize(cur_chrom_size);
            write_wig_binary(wig_name, cur_chrom, wig);
            wig.clear();
        }

    }
}
void read_wig(string& fname, genome_table& gt){
  //fixedStep
  ifstream ifstr(fname.c_str());
  assert(ifstr.good());

  //string header;
  char delim = ' ';
  char eq = '=';

  string line;
  vector<float> wig;
  string cur_chrom = "NA";
  int cur_contig_ind = -1;
  int cur_chrom_size = -1;
  int cur_step = -1;

  int cur_pos = -1;
  while(ifstr.good()){
    getline(ifstr, line);
    if(ifstr.good()){
      bool header = false;
      if(line.length() >= 9){
    if(line.substr(0, 9) == "fixedStep"){
      //cout<<"header "<<line<<endl;
      header = true;
    }
      }

      if(header){
    vector<string> header_fields = split(line, delim);
    assert(header_fields.size() > 0);
    assert(header_fields[0] == "fixedStep");

    string chrom = "none";
    int start = 0;
    int step = 1;

    for(unsigned int i=0; i<header_fields.size(); i++){
      vector<string> cur_fields = split(header_fields[i], eq);
      if(cur_fields.size() == 2){
        if(cur_fields[0] == "chrom") chrom = cur_fields[1];
        if(cur_fields[0] == "start") start = atoi(cur_fields[1].c_str());
        if(cur_fields[0] == "step") step = atoi(cur_fields[1].c_str());
      }
    }

    assert(step == 1);
    assert(chrom != "none");

    if(chrom != cur_chrom){ cout<<endl<<"Loading wig values for "<<chrom<<endl;
        // Create wigs array to store valuesi
        // Default values 0
        if (!(cur_chrom=="NA")){
            write_wig_binary(fname, cur_chrom, wig);
        }
        cur_chrom = chrom;
        cur_pos = start;
        cur_contig_ind = gt.contig_ind(cur_chrom); //contig_sizes[contig_ind];
        cur_chrom_size = gt.contig_sizes[cur_contig_ind];

        wig.clear();
        wig.resize(cur_chrom_size);
    }
    cur_chrom = chrom;
    cur_pos = start;
    cur_contig_ind = gt.contig_ind(cur_chrom); //contig_sizes[contig_ind];
    assert(cur_contig_ind >= 0);
    cur_step = step;
      } else {
    if(line.length() > 0){
      int coord = cur_pos - 1;
      if(cur_pos%100000 == 0){
        cout<<"\r "<<((double)coord)/1000000.0<<" M   ";
        cout.flush();
      }
      //assert(cur_contig_ind < (int)wig.size());

      if( !(coord<(int)cur_chrom_size)) {
        cout<<"coord: "<<cur_chrom<<"("<<cur_contig_ind<<") "<<coord<<" out of boundaries."<<endl;
        cout<<"cur_contig_size: "<<cur_chrom_size<<endl;
        exit(1);
      }
      wig[coord] = atof(line.c_str());
      cur_pos+=cur_step;
    }
      }
    }
  }
  write_wig_binary(fname, cur_chrom, wig);
  check_missing_wigs(fname, gt);
  ifstr.close();
  cout<<endl;
  return;
}

int main(int argc, char* argv[]){
    params pars(argc, argv);
    pars.require("genome_table", "genome_table", STRING_TYPE);
    pars.require("wig_file", "wig_file", STRING_TYPE);
    if(!pars.enforce()){
        exit(1);
    }
    string wig_fname = pars.get_string_value("wig_file");
    string gt_fname = pars.get_string_value("genome_table");
    genome_table gt(gt_fname);
    vector<float>  wigs;
    for(unsigned int i=0; i<gt.contig_sizes.size(); i++){
        int cur_contig_size = gt.contig_sizes[i];
        //vector<float> dummy_vec(cur_contig_size, 0);
        wigs.resize(cur_contig_size);
        string contig_name;
        contig_name = gt.contigs[i];
        cout << gt.contigs[i] << "\t" << gt.contig_sizes[i]<<endl;
    }

    read_wig(wig_fname, gt);

    return 0;
}
