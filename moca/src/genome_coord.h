#ifndef GENOME_COORD_H
#define GENOME_COORD_H
#include <vector>
#include <string>
#include <map>

using std::vector;
using std::string;

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


#endif
