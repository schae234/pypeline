#!/usr/bin/python
from __future__ import print_function,with_function
import sys
import re
from collection import defaultdict


class RepeatMasker(object):
    def __init__(self,repeatMaskerFile):
        self.repeat = defaultdict(lambda: defaultdict(list))
        with open(repeatMaskerFile,'r') as IN_REP:
            IN_REP.readline()
            IN_REP.readline()
            IN_REP.readline()  
            for line in IN_REP:
                line = line.strip()
                score,pdiv,pdel,pins,chrom,beg,end,left,cplus,match,rep_class,rbeg,rend,rleft,id = line.split()
                repeat[chrom]['start'].append(beg)
                repeat[chrom]['end'].append(end)
 
if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i','--input_vcf',type=str,help="Input VCF files to merge. Multiple VCF files accepted.")
    parser.add_option('--keepLowQual',default=False,action="store_true",help="Keep Low Qual Variants")
    parser.add_option('--filter',type=str,default=None,help="The name of the field in the INFO section to filter on")
    parser.add_option('--cutoff',type=float,default=None,help="The cutoff for the field in the INFO section")
    parser.add_option('--biallelic',action="store_true",default=False,help="filter out variants which are not bi-allelic")
    parser.add_option('--repeat_masker',type=str,default=None,help="filter out variants within repetitive regions, expects a repeat masker file as input.")
    options,args = parser.parse_args(sys.argv[1:])

    if options.repeat_masker:
        repeat = RepeatMasker(options.repeat_masker)

    import pdb; pdb.set_trace()

    with open(options.input_vcf,'r') as IN_VCF:
        for line in IN_VCF:
            line = line.strip()
            if line.startswith('#'):
                print(line)
            else:
                fields = line.split()
                if options.keepLowQual == False and 'LowQual' in fields[6]:
                    continue
                filter_score = re.search(str(options.filter+'=([^;]*)(;?)'),fields[7])
                if filter_score == None:
                    continue
                if float(filter_score.group(1)) < options.cutoff:
                    continue
                if options.biallelic and len(fields[4]) > 1:
                    continue
                print(line)
                
                
