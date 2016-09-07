#!/usr/bin/python
from __future__ import print_function

import sys

class SnpList(object):
    
    def __init__(self):
        pass

    def read_vcf(self,vcf_file):
        pass



if __name__ == '__main__':
    from optparse import OptionParser
    
    def split_comma(option,opt,value,parser):
        ''' split a options into list of values '''
        setattr(parser.values, option.dest, value.split(','))

    parser = OptionParser()
    parser.add_option('--vcf',type=str,action='callback',callback=split_comma,help='List of comma seperated bam files')
    options,args = parser.parse_args(sys.argv[1:])

    
