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
#include "crow_all.h"
#include "params.h"
#include "string_utils.h"
#include "genome_table.h"
#include "math_functions.h"
#include "thirdparty/INIReader.h"

using std::ifstream;
using std::ofstream;
using std::istringstream;
using std::ostringstream;
using std::cerr;
using std::endl;
using std::cout;
using std::unordered_map;

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

void write_wig_binary(string genome_name, genome_table &gt, vector<vector<float> > &wig){
        //cur_contig_ind = gt.contig_ind(cur_chrom); //contig_sizes[contig_ind];
        //cur_chrom_size = gt.contig_sizes[cur_contig_ind];
    string binary_path;
    for(size_t i = 0; i < wig.size(); i++ )
    {
        ostringstream index;
        index<<i;
        binary_path = genome_name +  "_chr_" + index.str() + ".bin";
        ofstream wig_binary (binary_path.c_str(), ofstream::binary);
        //if ( wig[i].size() > 0 )
        //{
            const char* buffer = reinterpret_cast<const char*>(&wig[i][0]);
            wig_binary.write(buffer, wig[i].size()*sizeof(float));
        //}
        wig_binary.close();
    }
    vector<int> wig_sizes(wig.size());
    for (size_t i=0; i< wig.size(); i++){
         wig_sizes[i]= wig[i].size();
    }
    binary_path = genome_name +  "_contig_size.map";
    ofstream wig_binary (binary_path.c_str(), ofstream::binary);
    const char* buffer = reinterpret_cast<const char*>(&wig_sizes[0]);

    wig_binary.write(buffer,wig_sizes.size() * sizeof(wig_sizes[0]));
    wig_binary.close();


    for(size_t i=0; i<gt.contig_sizes.size(); i++){
        cout<<"wig wrote: "<<i<<wig_sizes[i]<<endl;
    }

    /*//Read to check if all okay
    ifstream size_binary(binary_path.c_str(), std::ios::in | std::ios::binary | std::ios::ate);// | ifstream::binary);
    size_t filesize = size_binary.tellg()/sizeof(int);
    std::vector<int> read_wig_sizes(filesize, 0);
    cout<<"Number of chromsomes read: "<<filesize<<endl;
    size_binary.seekg(0, std::ios::beg);

    size_binary.read(reinterpret_cast<char*>(&read_wig_sizes[0]), read_wig_sizes.size()*sizeof(read_wig_sizes[0]));
    size_binary.close();
    for(size_t i=0; i<gt.contig_sizes.size(); i++){
        cout<<"wig: "<<i<<" read: "<<read_wig_sizes[i]<<" wrote: "<<wig_sizes[i]<<endl;
    }*/
}

// Assume if a binary is present all binaries would exists/
//
bool can_read_binary(string genome_name, genome_table& gt){
    string binary_path;
    for(size_t i=0; i<gt.contig_sizes.size(); i++){
        ostringstream index;
        index<<i;
        binary_path = genome_name +  "_chr_" + index.str()+ ".bin";
        ifstream wig_binary(binary_path.c_str(), ifstream::binary);
        if(!wig_binary.good()){
            cerr<<"Did not find bin file: "<<binary_path<<endl;
            cout<<"Building all binary files..."<<endl;
            return false;
        }
    }
    return true;
}

vector<vector<float> > read_wig_binary(genome_table& gt, string genome_name){
    vector<vector<float> > wigs;
    string binary_path;
    binary_path = genome_name +  "_contig_size.map";
    ifstream size_binary(binary_path.c_str(), std::ios::in | std::ios::binary | std::ios::ate);// | ifstream::binary);
    size_t filesize = size_binary.tellg()/sizeof(int);
    std::vector<int> wig_sizes(filesize, 0);
    //cout<<"Number of chromsomes read: "<<filesize<<endl;
    size_binary.seekg(0, std::ios::beg);

    size_binary.read(reinterpret_cast<char*>(&wig_sizes[0]), wig_sizes.size()*sizeof(wig_sizes[0]));
    size_binary.close();
    for(size_t i=0; i<gt.contig_sizes.size(); i++){
        ostringstream index;
        index<<i;
        binary_path = genome_name +  "_chr_" + index.str() + ".bin";
        ifstream wig_binary(binary_path.c_str(), std::ios::binary);// | std::ios::ate | ifstream::binary);
        int cur_contig_size = wig_sizes[i];//gt.contig_sizes[i];
        vector<float> values(cur_contig_size,0);
        wig_binary.read((char*)(&values[0]),cur_contig_size*sizeof(float));
        wigs.push_back(values);
        wig_binary.close();
     }
    return wigs;
}

void calculate_scores(vector<genome_region>&regions, genome_table &gt, vector<vector<double> > &scores, string &output_fname,unordered_map<int, vector<float> > wigs, int &flank){

  string distri_out_fname = output_fname + ".distr";


  for(unsigned int i=0; i<regions.size(); i++){
    int cur_contig_ind = gt.contig_ind(regions[i].chrom);
    int start = regions[i].start;
    int end = regions[i].end;
    char strand = regions[i].strand;
    ofstream ofstr(distri_out_fname.c_str());
     if(!ofstr.good()){
       cout<<"Bad file: "<<output_fname<<endl;
       assert(ofstr.good());
    }

    vector<double> cur_scores;
    int region_size = regions[0].end - regions[0].start;
    //cout<<"Line: "<<i+1<<endl;
    if(cur_contig_ind != -1){
        ofstr<<regions[i].chrom<<"_"<<start<<"_"<<end<<"_"<<strand;
        //cout<<"Chr: "<<regions[i].chrom<<endl;
        if(regions[i].strand == '+'){
        for(int j=-flank; j<region_size+flank; j++){
          //cout<<"Current contig: " << cur_contig_ind << "Starting at: " << start << " Accessing: "<<start+j-1<<endl;
          ofstr<<"\t"<<wigs[cur_contig_ind].at(start+j-1);
          cur_scores.push_back(wigs[cur_contig_ind].at(start+j-1));
        }
        //if(regions[i].p_value <= 0.000001)
        scores.push_back(cur_scores);
        ofstr<<endl;
        }
        if(regions[i].strand == '-'){
            //vector<double> cur_scores;
            for(int j=-flank; j<region_size + flank; j++){
                ofstr<<"\t"<<wigs[cur_contig_ind].at(end-2-j);
                cur_scores.push_back(wigs[cur_contig_ind].at(end-2-j));
            }
            //if(regions[i].p_value <= 0.000001)
            scores.push_back(cur_scores);
            vector<double>().swap(cur_scores);
            ofstr<<endl;
        }
    }else {
      cout<<"Couldn't find "<<regions[i].chrom<<" in the genome table"<<endl;
      cout<<"Skipping. "<<endl;
    }
  }

}

void read_regions(string input_fname, vector<genome_region> &regions){
  ifstream ifstr(input_fname.c_str());
  assert(ifstr.good());

  vector<vector<double> > scores;
  char tab_char = '\t';
  string line;
  while(ifstr.good()){
    getline(ifstr, line);
    if(ifstr.good()){
        if(line.size() > 0){
            if(line[0] != '#'){
              vector<string> line_fields = split(line, tab_char);
              assert(line_fields.size() >= 4);
              genome_region new_region;
              new_region.chrom = line_fields[0];
              new_region.start = atoi(line_fields[1].c_str());
              new_region.end = atoi(line_fields[2].c_str());
              new_region.strand = line_fields[3][0];
              new_region.p_value = atof(line_fields[4].c_str());
              new_region.q_value = atof(line_fields[5].c_str());
              regions.push_back(new_region);
            }
        }
    }
  }
}

void write_stats(string &output_fname, vector<genome_region> &regions, vector<vector<double> > &scores, int &flank){
  //cout<<"Writing stats: "<<output_fname<<endl;
  string output_stats_fname = output_fname + ".stats";
  ofstream stats_ofstr(output_stats_fname.c_str());
  assert(stats_ofstr.good());
  int region_size = regions[0].end - regions[0].start;
  for(int i=-flank; i<region_size+flank; i++){
    vector<double> this_base_scores;
    for(unsigned int j=0; j<scores.size(); j++){
      int offset = i+flank;
      this_base_scores.push_back(scores[j].at(offset));
    }
    int n = this_base_scores.size();
    double cur_mean = mean(this_base_scores);
    double cur_stdev = stdev(this_base_scores)/sqrt((double)n);
    stats_ofstr<<i<<"\t"<<cur_mean<<"\t"<<cur_stdev<<endl;
  }
}

void read_wig(string &wig_name, string &chr, vector<float> &wig, genome_table &gt){
    string binary_path;
    binary_path = wig_name +  "__" + chr + ".wigbin";
    int cur_contig_ind=-1;
    int cur_contig_size;
    //cout <<"Reading: "<<binary_path<<endl;
    ifstream wig_binary(binary_path.c_str(), std::ios::binary);// | std::ios::ate | ifstream::binary);
    if(!wig_binary.good()){
        cerr<<"Error reading file: "<<binary_path<<endl;
        exit(1);
    }
    cur_contig_ind = gt.contig_ind(chr);
    cur_contig_size = gt.contig_sizes[cur_contig_ind];
    vector<float> values(cur_contig_size,0);
    wig_binary.read((char*)(&values[0]),cur_contig_size*sizeof(float));
    wig=values;
    wig_binary.close();
}

void read_bin_wigs_one_by_one(string &wig_name, string output_fname, vector<genome_region> &regions, genome_table &gt, int &flank ){
    string distri_out_fname = output_fname + ".distr";
    string prev_chr = "NA";
    string cur_chr;
    vector<float> wig;
    vector<vector<double> > scores;
    int cur_contig_ind=-1;
    int start=-1;
    int end=-1;
    char strand;
    int region_size=0;
    vector<double> cur_scores;
    ofstream ofstr(distri_out_fname.c_str());
    if(!ofstr.good()){
       cout<<"Bad file: "<<output_fname<<endl;
       assert(ofstr.good());
    }
    for(unsigned int i=0; i<regions.size(); i++){
        cur_chr = regions[i].chrom;
        if (cur_chr!=prev_chr){
            vector<float>().swap(wig);
            read_wig(wig_name, cur_chr, wig, gt);
            prev_chr = cur_chr;
        }
    cur_contig_ind = gt.contig_ind(regions[i].chrom);
    start = regions[i].start;
    end = regions[i].end;
    strand = regions[i].strand;
    region_size = regions[0].end - regions[0].start;
    if(cur_contig_ind != -1){
        ofstr<<regions[i].chrom<<"_"<<start<<"_"<<end<<"_"<<strand;
        //cout<<"Chr: "<<regions[i].chrom<<endl;
        if(regions[i].strand == '+'){
        for(int j=-flank; j<region_size+flank; j++){
          ofstr<<"\t"<<wig.at(start+j-1);
          cur_scores.push_back(wig.at(start+j-1));
        }
        //if(regions[i].p_value <= 0.000001)
        scores.push_back(cur_scores);
        ofstr<<endl;
        }
        if(regions[i].strand == '-'){
            //vector<double> cur_scores;
            for(int j=-flank; j<region_size + flank; j++){
                ofstr<<"\t"<<wig.at(end-2-j);
                cur_scores.push_back(wig.at(end-2-j));
            }
            //if(regions[i].p_value <= 0.000001)
            scores.push_back(cur_scores);
            vector<double>().swap(cur_scores);
            ofstr<<endl;
        }
    }else {
      cout<<"Couldn't find "<<regions[i].chrom<<" in the genome table"<<endl;
      cout<<"Skipping. "<<endl;
    }
  }
    write_stats(output_fname, regions, scores, flank);
    vector<vector<double> >().swap(scores);
}


void read_bin_wigs(string &wig_name, unordered_map<int, vector<float> > &wigs, vector<string> &chr_toread, genome_table &gt, int &flank){
    string binary_path;
    int cur_contig_ind;
    int cur_contig_size;
    for (unsigned int i=0;i<chr_toread.size(); i++){
        binary_path = wig_name +  "__" + chr_toread[i] + ".wigbin";
        //cout <<"Reading: "<<binary_path<<endl;
        ifstream wig_binary(binary_path.c_str(), std::ios::binary);// | std::ios::ate | ifstream::binary);
        if(!wig_binary.good()){
            cerr<<"Error reading file: "<<binary_path<<endl;
            exit(1);
        }
        cur_contig_ind = gt.contig_ind(chr_toread[i]);
        cur_contig_size = gt.contig_sizes[cur_contig_ind];
        vector<float> values(cur_contig_size,0);
        wig_binary.read((char*)(&values[0]),cur_contig_size*sizeof(float));
        wigs[cur_contig_ind] = values;
        wig_binary.close();
    }
}

/*void create_profiles(string input_fname, string output_fname, genome_table &gt, string &wig_name, int &flank){//, vector<vector<double> > wigs){
  vector<genome_region> regions;
  read_regions(input_fname, regions);
  vector<int> indices;
  vector<string> chr_toread;
  unordered_map<int, vector<float> > wigs;
  for(unsigned int i=0;i<regions.size();i++){
      int cur_contig_ind = gt.contig_ind(regions[i].chrom);
      if (std::find(indices.begin(), indices.end(), cur_contig_ind) == indices.end()) {
          indices.push_back(cur_contig_ind);
          chr_toread.push_back(regions[i].chrom);
      }
      cout<<regions[i].chrom<<endl;
  }
  read_bin_wigs(wig_name, wigs, chr_toread, gt, flank);
  vector<vector<double> > scores;
  calculate_scores(regions, gt, scores, output_fname, wigs, flank);
  write_stats(flank, regions, scores, output_fname);
}*/

void create_profiles(string output_fname, vector<genome_region> &regions, genome_table &gt, unordered_map<int, vector<float> > wigs, int &flank){
  vector<vector<double> > scores;
  //calculate_scores(regions, gt, scores, output_fname, wigs, flank);
 // write_stats(flank, regions, scores, output_fname);
}

vector<string> determine_chr_to_read(vector<vector<genome_region> > & regions, genome_table &gt){
    int cur_contig_ind;
    vector<int> indices;
    vector<string> chr_toread;
    for (unsigned int i=0; i<regions.size(); i++){
        for(unsigned int j=0;j<regions[i].size();j++){
            cur_contig_ind = gt.contig_ind(regions[i][j].chrom);
            if (std::find(indices.begin(), indices.end(), cur_contig_ind) == indices.end()) {
                indices.push_back(cur_contig_ind);
                chr_toread.push_back(regions[i][j].chrom);
            }
        }
    }
    return chr_toread;
}

/*int main(int argc, char* argv[]){
  srand(time(NULL));

  params pars(argc, argv);

  pars.require("sample_sites_file", "sample_sites_file", STRING_TYPE);
  pars.require("control_sites_file", "control_sites_file", STRING_TYPE);
  pars.require("genome_table", "genome_table", STRING_TYPE);
  pars.require("wig_file", "wig_file", STRING_TYPE);
  pars.require("sample_outfile", "sample_outfile", STRING_TYPE);
  pars.require("control_outfile", "control_outfile", STRING_TYPE);
  pars.optional("flank", "flank", "0", INT_TYPE);

  if(!pars.enforce()){
    exit(1);
  }

  string sample_fname = pars.get_string_value("sample_sites_file");
  string control_fname = pars.get_string_value("control_sites_file");

  string sample_out_fname = pars.get_string_value("sample_outfile");
  string control_out_fname = pars.get_string_value("control_outfile");

  string wig_fname = pars.get_string_value("wig_file");
  string gt_fname = pars.get_string_value("genome_table");//analysis_path + genome_table_suffix;
  int flank = pars.get_int_value("flank");



  genome_table gt(gt_fname);
  vector<vector<genome_region> > regions;

  vector<genome_region> sample_region;
  vector<genome_region> control_region;

  read_regions(sample_fname, sample_region);
  read_regions(control_fname, control_region);

  regions.push_back(sample_region);
  //It is possible that the control regions are not found, so we simply zero out everything
  regions.push_back(control_region);
  bool control_regions_absent = false;
  if (control_region.size()==0){
       control_regions_absent = true;
  }
  vector<string> chr_toread;
  chr_toread = determine_chr_to_read(regions, gt);
  read_bin_wigs_one_by_one(wig_fname, sample_out_fname, sample_region, gt, flank);
  if (!(control_regions_absent)){
      read_bin_wigs_one_by_one(wig_fname, control_out_fname, control_region, gt, flank);
  }
  else{
      string stats_out_fname = control_out_fname + ".stats";
      ofstream stats_ofstr(stats_out_fname.c_str());
      if(!stats_ofstr.good()){
          cout<<"Bad file: "<<stats_out_fname<<endl;
            assert(stats_ofstr.good());
        }
      int region_size = 0;
      region_size = sample_region[0].end - sample_region[0].start;
      for(int j=-flank; j<region_size+flank; j++){
          int cur_mean = 0;
          int cur_stdev = 0;
          stats_ofstr<<j<<"\t"<<cur_mean<<"\t"<<cur_stdev<<endl;
      }
  }
  //create_profiles(sample_out_fname, gt, wig_fname, flank);//, vector<vector<double> > wigs){
  //create_profiles(control_fname, control_out_fname, gt, wig_fname, flank);//, vector<vector<double> > wigs){
  return 0;
}*/


int main()
{

    crow::SimpleApp app;
    INIReader reader("/home/saket/application.cfg");
    if (reader.ParseError() < 0) {
                std::cout << "Can't load 'test.ini'\n";
                        return 1;
    }
    std::set<std::string> sections = reader.GetSections();
    //i
    const std::string genome = "genome";
    for (const std::string& section : sections)
     {
         //std::cout << section << ' ' << std::endl;
         if (strncmp(section.c_str(), genome.c_str(), strlen(genome.c_str()))==0){
             std::set<std::string> fields = reader.GetFields(section);
              for (const std::string& field : fields)
              {
                    std::cout << field << ' ' << std::endl;

              }
         }

     }

    CROW_ROUTE(app, "/")([](){
        return "Hello world";
    });

    app.port(18080).multithreaded().run();
}
