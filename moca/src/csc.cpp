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
#include <algorithm>
#include <iterator>
#include <vector>
#include <unordered_map>

#include "string_utils.h"
#include "genome_table.h"
#include "math_functions.h"
#include "genome_coord.h"

using std::ifstream;
using std::ofstream;
using std::istringstream;
using std::ostringstream;
using std::cerr;
using std::endl;
using std::cout;
using std::unordered_map;

bool pos_less(const genome_coord& l, const genome_coord& r){
  return l.pos < r.pos;
}


void read_wig(string& fname, genome_table& gt, vector<vector<float> >& wig){
  //fixedStep
  ifstream ifstr(fname.c_str());
  assert(ifstr.good());

  //string header;
  char delim = ' ';
  char eq = '=';

  string line;
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

            if(chrom != cur_chrom){ cout<<endl<<"Loading wig values for "<<chrom<<endl;}
            cur_chrom = chrom;
            cur_pos = start;
            cur_contig_ind = gt.contig_ind(cur_chrom); //contig_sizes[contig_ind];
            cur_chrom_size = gt.contig_sizes[cur_contig_ind];
            assert(cur_contig_ind >= 0);
            cur_step = step;
        }
        else {
            if(line.length() > 0){
                int coord = cur_pos - 1;
                if(cur_pos%100000 == 0){
                    cout<<"\r "<<((double)coord)/1000000.0<<" M   ";
                    cout.flush();
                }
                assert(cur_contig_ind < (int)wig.size());

                if( !(coord<(int)wig[cur_contig_ind].size()) ){
                    cout<<"coord: "<<cur_chrom<<"("<<cur_contig_ind<<") "<<coord<<" out of boundaries."<<endl;
                    cout<<"cur_contig_size: "<<wig[cur_contig_ind].size()<<endl;
                    exit(1);
                }
                assert(coord< (int)wig[cur_contig_ind].size());
                wig[cur_contig_ind][coord] = atof(line.c_str());
                cur_pos+=cur_step;
            }
        }
    }
  }
  ifstr.close();
  cout<<endl;
  return;
}

