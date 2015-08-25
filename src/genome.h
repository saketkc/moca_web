#ifndef GENOME_H
#define GENOME_H

#include <vector>
#include <map>
#include <fstream>
#include <iostream>


class chrom{
 public:
  std::string name; //name following '>' any characters are allowed
  std::string seq;
  
  long begin; //file position of the first base
  long end; //file position after the last base

  //std::ios::pos_type begin;
  //std::ios::pos_type end;

  bool loaded;
  chrom(){loaded = false;} 
};

class genome{
 public:
  std::string genome_fname;
  std::string genome_filemap_fname;

  std::vector<chrom> chroms;

  std::map<std::string, int> chrom_map; //to quickly search chroms for a specific chrom
  
 private:
  std::ifstream genome_ifstr;
  std::ifstream genome_filemap_ifstr;

  std::string cur_chrom;
  int cur_chrom_ind;

 public:
  genome(std::string _genome_fname);
  ~genome();
  void build_filemap();
  int load(const std::string& chrom, bool erase_prev); //loads the whole chrom into the memory
  //previous is erased or kept
  std::string get_seq(const std::string& chrom, long coord, int length, bool erase_prev);
  bool chrom_exists(std::string& chrom);
};

std::string reverse_complement(const std::string& _seq);

#endif
