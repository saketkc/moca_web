%module csc
%{
#include "string_utils.h"
#include "genome_table.h"
#include "math_functions.h"
#include "genome_coord.h"
extern void read_wig(string& fname, genome_table& gt, vector<vector<float> >& wig);
%}
%include "std_vector.i"
%include "std_string.i"
namespace std {
    %template(IntVector) vector<int>;
    %template(UIntVector) vector<unsigned int>;
    %template(DoubleVector) vector<double>;
    %template(StringVector) vector<string>;
    %template(ConstCharVector) vector<const char*>;
    %template(ConstStringViewVector) vector<StringView>;
    %template(ChromInfoVector) vector<chrom_info>;

}

%include "genome_table.h"
%include "string_utils.cpp"
extern void read_wig(string& fname, genome_table& gt, vector<vector<float> >& wig);

