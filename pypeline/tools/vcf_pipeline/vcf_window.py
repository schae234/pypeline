#!/usr/bin/python2

from __future__ import print_function
import os
import sys
import numpy
import re
import bisect
import time
from optparse import OptionParser
from collections import defaultdict

class VCFWindow(object):
    def __init__(self):
        # A list of tuples containing the chromosome and window number
        self.windows = []
        self.win_chroms = []
        self.num_windows = 0
        self.win_size = 50000
        self.verbose = False
        self.log_file = sys.stderr
        self.out = sys.stdout

    def populate_window(self,vcf):
        cur_win = 1
        cur_chrom = None
        with open(vcf,'r') as file:
            for line_num,line in enumerate(file):
                if line.startswith('#'):
                    continue
                # we are at variants
                fields = line.strip().split()
                if self.verbose and line_num % 1000000 == 0:
                        self.log("On line {}".format(line_num))
                # start over for new chromosomes
                if fields[0] != cur_chrom:
                    cur_win = 1
                    cur_chrom = fields[0]
                while int(fields[1]) > cur_win*self.win_size:
                    cur_win+=1
                    self.num_windows += 1
                self.windows.append(cur_win)
                self.win_chroms.append(cur_chrom)

    def process(self,vcf):
        with open(vcf,'r') as file:
            cur_window = self.windows[0]
            cur_chrom = self.win_chroms[0]
            pool = []
            line_num = 0
            for line in file:
                if line.startswith('#'):
                    continue
                # we are at variants
                fields = line.strip().split()
                if self.windows[line_num] == cur_window:
                    pool.append(fields)
                else:
                    #self.process_pool(pool)
                    print("{},{},{}".format(len(pool),cur_chrom,cur_window))
                    pool = []
                    cur_window = self.windows[line_num]
                    cur_chrom = self.win_chroms[line_num]
                    pool.append(fields)
                line_num += 1
               
 
    def process_pool(self,pool):
        print(len(pool))

    def log(self,*args):
        print(time.ctime(),' - ',*args,file=self.log_file)
                   
    def emit(self,*args):
        print(*args,file=self.out) 
         

def main(argv):
    parser = OptionParser()
    parser.add_option('--verbose',default=False,action='store_true',help="verbose level")
    options, args = parser.parse_args(argv) 
    win = VCFWindow()
    win.__dict__.update(options.__dict__)
    for filename in args:
        win.populate_window(filename)
        win.process(filename)
    

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
