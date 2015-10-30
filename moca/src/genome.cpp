#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>

#include <stdlib.h>
#ifndef _ASSERT_H
#include "assert.h"
#endif

//#inlcude "string_utils.h"

using std::vector;
using std::map;
using std::string;
using std::cout;
using std::cerr;
using std::endl;

#include "genome.h"

std::vector<string> split(const string& inp_string, char sep);

bool genome::chrom_exists(std::string& chrom){
  map<string, int>::iterator it = chrom_map.find(chrom);

  if(it == chrom_map.end()){ return false; } //no such chrom
  else return true;
}

genome::genome(string _genome_fname){
  genome_fname = _genome_fname;
  genome_filemap_fname = _genome_fname + ".filemap";

  cur_chrom = "";
  cur_chrom_ind = -1;

  genome_ifstr.open(genome_fname.c_str());
  if(!genome_ifstr.good()){
    cerr<<"Bad file name: "<<_genome_fname<<endl;
    exit(1);
  }

  cout<<"checking for the filemap"<<endl;
  genome_filemap_ifstr.open(genome_filemap_fname.c_str());
  if(!genome_filemap_ifstr.good()){
    cout<<"Filemap for genome file does not exist."<<endl;
    cout<<"Building the filemap"<<endl;

    genome_filemap_ifstr.close();
    build_filemap();

    genome_filemap_ifstr.open(genome_filemap_fname.c_str());
    if(!genome_filemap_ifstr.good()){
      cerr<<"Failed to build a filemap. Check the write permissions."<<endl;
      exit(1);
    }
  }


  while(genome_filemap_ifstr.good()){
    string cur_line;
    getline(genome_filemap_ifstr, cur_line);

    if(genome_filemap_ifstr.good()){
      vector<string> cur_line_fields = split(cur_line, '\t');
      assert(cur_line_fields.size() == 3);
      chrom new_chrom;
      new_chrom.name = cur_line_fields[0];
      new_chrom.begin = atol(cur_line_fields[1].c_str());
      new_chrom.end = atol(cur_line_fields[2].c_str());
      new_chrom.loaded = false;

      chroms.push_back(new_chrom);
      chrom_map[new_chrom.name] = chroms.size()-1;
      //cout<<cur_line_fields[0]<<" "<<cur_line_fields[1]<<endl;
    }
  }
  cout<<"Read "<<chroms.size()<<" chroms from filemap"<<endl;

  //for(unsigned int i=0; i<chroms.size(); i++){
  //  cout<<chroms[i].name<<" "<<chroms[i].begin<<" "<<chroms[i].end<<endl;
  //}
}

void genome::build_filemap(){
  std::ofstream filemap_ofstr(genome_filemap_fname.c_str());
  if(!filemap_ofstr.good()){
    cerr<<"Failed to create a filemap file: "<<genome_filemap_fname<<endl;
    cerr<<"Check your file permissions."<<endl;
    exit(1);
  }

  assert(genome_ifstr.good());

  string cur_chrom = "";
  long cur_chrom_begin = 0;
  long cur_file_pos = -1;

  while(genome_ifstr.good()){
    string cur_line;
    cur_file_pos = genome_ifstr.tellg();
    getline(genome_ifstr, cur_line);
    if(genome_ifstr.good()){

      if(cur_line.length() > 0){
	if(cur_line[0] == '>'){
	  if(cur_chrom != ""){
	    filemap_ofstr<<cur_chrom<<"\t"<<cur_chrom_begin<<"\t"<<cur_file_pos<<endl;
	    cout<<cur_chrom<<"\t"<<cur_chrom_begin<<"\t"<<cur_file_pos<<endl;
	  }
	  cur_chrom = cur_line.substr(1, cur_line.length()-1);
	  cur_chrom_begin = genome_ifstr.tellg();
	}
      }
    }
  }

  //save the last contig
  filemap_ofstr<<cur_chrom<<"\t"<<cur_chrom_begin<<"\t"<<cur_file_pos<<endl;
  cout<<"last: "<<cur_chrom<<"\t"<<cur_chrom_begin<<"\t"<<cur_file_pos<<endl;
  filemap_ofstr.close();
}

int genome::load(const string& chrom, bool erase_prev){

  if(cur_chrom == chrom){
    //cout<<chrom<<" already loaded"<<endl;
    return 1;
  }
  //cout<<endl;
  //cout<<"loading "<<chrom<<endl;
  //cout<<endl;

  //int chrom_ind = -1;
  //for(unsigned int i=0; i<chroms.size() && (chrom_ind == -1); i++){
  //  if(chrom == chroms[i].name){
  //    chrom_ind = i;
  //  }
  //}
  //if(chrom_ind == -1) return -1; //no such contig

  map<string, int>::iterator it = chrom_map.find(chrom);

  if(it == chrom_map.end()){ cout<<"loading "<<chrom<<endl; return -1; } //no such chrom

  int chrom_ind = it->second;
  assert(chroms[chrom_ind].name == chrom);
  //cout<<"chrom_ind: "<<chrom_ind<<" loaded: "<<chroms[chrom_ind].loaded<<endl;

  if(erase_prev){
    if(cur_chrom_ind != -1){
      //unload the previous sequence
      chroms[cur_chrom_ind].seq.clear();
      chroms[cur_chrom_ind].seq.reserve(0);
      chroms[cur_chrom_ind].loaded = false;
      cout<<"erasing prev: "<<chroms[cur_chrom_ind].name<<endl;
    }
  }

  cur_chrom_ind = chrom_ind;
  cur_chrom = chrom;

  if(chroms[chrom_ind].loaded){
    //cout<<chroms[chrom_ind].name<<" already loaded. skipping."<<endl;
    return 1;
  } else {

    if(!genome_ifstr.good()){
      genome_ifstr.clear();
      genome_ifstr.seekg(0);
      assert(genome_ifstr.good());
    }

    int __length = chroms[chrom_ind].end - chroms[chrom_ind].begin;
    //parse the sequence

    string tmp_seq(__length, 42);
    vector<unsigned int> new_line_coords;


    //genome_ifstr.seekg(0, std::ios::end);
    //cout<<"total file length : "<<genome_ifstr.tellg()<<endl;
    //cout<<"shifting to       : "<<chroms[chrom_ind].begin<<endl;

    genome_ifstr.seekg(chroms[chrom_ind].begin, std::ios::beg);
    //cout<<"cur_pos           : "<<genome_ifstr.tellg()<<endl;

    genome_ifstr.read((char*)(&tmp_seq[0]), __length*sizeof(char));
    for(unsigned int i=0; i<tmp_seq.size(); i++){
      if(tmp_seq[i] == '\n'){
	//cout<<i<<endl;
	new_line_coords.push_back(i);
      }
    }

    chroms[chrom_ind].seq = "";
    chroms[chrom_ind].seq.reserve(__length);
    for(unsigned int i=0; i<new_line_coords.size(); i++){
      if(i==0){
	chroms[chrom_ind].seq += tmp_seq.substr(0, new_line_coords[0]);
      } else {
	chroms[chrom_ind].seq += tmp_seq.substr(new_line_coords[i-1]+1, new_line_coords[i] - new_line_coords[i-1]-1);
      }
    }
    chroms[chrom_ind].seq += tmp_seq.substr(new_line_coords[new_line_coords.size()-1]+1,
					    tmp_seq.size() - new_line_coords[new_line_coords.size()-1]- 1);

    cout<<"loaded: "<<chroms[cur_chrom_ind].seq.length()<<" bps from "<<chroms[cur_chrom_ind].name<<endl;
    tmp_seq = "";

    chroms[chrom_ind].loaded = true;
    return 1;
  }
}

string genome::get_seq(const string& chrom, long coord, int length, bool erase_prev){
  string res="";
  int load_res = load(chrom, erase_prev);
  if(load_res == -1){
    cerr<<"Error. No such chrom: "<<chrom<<endl;
    exit(1);
  }

  if(coord >= (int) chroms[cur_chrom_ind].seq.size() || coord + length >= (int) chroms[cur_chrom_ind].seq.size()){
    cerr<<"Extracting: "<<chrom<<" "<<coord<<"-"<<coord+length<<endl;
    cerr<<"chrom size: "<<chroms[cur_chrom_ind].seq.size()<<endl;
    cerr<<"Error. Attempting extract sequence past the chrom boundary"<<endl;
    //exit(1);
    return res;
  }

  if(coord < 0){
    cout<<"Warning! "<<coord<<" < 0"<<endl;
    coord = 0;
    return res;
  }
  if((int) chroms[cur_chrom_ind].seq.size() > coord + length){
    res = chroms[cur_chrom_ind].seq.substr(coord, length);
  } else {
    res = chroms[cur_chrom_ind].seq.substr(coord, chroms[cur_chrom_ind].seq.size() - coord);
  }
  return res;
}

genome::~genome(){
  genome_ifstr.close();
  genome_filemap_ifstr.close();
}

char _complement(char c){
  if(c == 'N') return 'N';
  if(c == 'A') return 'T';
  if(c == 'T') return 'A';
  if(c == 'G') return 'C';
  if(c == 'C') return 'G';

  if(c == 'n') return 'N';
  if(c == 'a') return 'T';
  if(c == 't') return 'A';
  if(c == 'g') return 'C';
  if(c == 'c') return 'G';

  assert(false);
  char res = '*';
  return res;
}

string reverse_complement(const string& _seq){
  string res;
  for(int i=_seq.size()-1; i>=0; i--){
    char cur_char = _seq[i];

    res.push_back(_complement(cur_char));
  }
  return res;

}
