#!/usr/bin/python
from __future__ import print_function,with_statement,division
from optparse import OptionParser
import sys
import re
from collections import defaultdict

class VCF_PR(object):
    verbose = False

    def __init__(self,map_file,report_file):
        self.snp_map = defaultdict(dict)
        self.gold = defaultdict(dict)
        self.num_gold = 0
        self.populate_map_file(map_file)
        self.populate_final_report(report_file)

    def populate_map_file(self, map_file):
        ''' Create mapping between snp id an position '''
        with open(map_file,'r') as map_file:
            for line in map_file:
                chr, id, cm, pos = line.strip().split()
                self.snp_map[chr][pos] = id
        
    def populate_final_report(self, report_file):
        '''  Read in Final Report  '''
        with open(report_file,'r') as report:
            while not "[Data]" == report.readline().strip():
                pass
            header = report.readline()
            for line in report:
               snp,id,f1,f2,t1,t2,ab1,ab2,gc,x,y = line.strip().split()
               self.gold[id][snp] = {
                   'top':sorted([t1,t2]),
                   'for':sorted([f1,f2]),
                   'ab' :sorted([ab1,ab2])
               }
               self.num_gold += 1

    def relevent(self, vcf_file, rank='VQSLOD'):
        ''' Returns list of ranked Values for T/F '''
        unranked_list = list()
        indiv = list()
        with open(vcf_file,'r') as file:
            for line in file:
                if line.startswith('##'):  # meta dat line
                    continue
                elif line.startswith("#"): # header line
                    indiv = line.strip().split()[9:]
                else:                      # Variant line
                    fields = line.strip().split()
                    inds = fields[9:]
                    chrom = fields[0].replace('chr','')
                    pos = fields[1]
                    filter = fields[6]
                    if filter == 'LowQual' or chrom not in self.snp_map or pos not in self.snp_map[chrom]:
                        continue
                    # Extract the score
                    if rank == 'QUAL':
                        score = fields[5]
                    else:
                        score = float(re.search(str(rank+'=(.*);'),fields[7]).group(1) )
                    for i,ind in enumerate(indiv):
                        # skip indiv not in gold standard
                        if ind not in self.gold:
                            continue
                        genos = inds[i].split(':')[0].replace('0',fields[3]).replace('1',fields[4]).split('/')
                        genos.sort()
                        snp_name = self.snp_map[chrom][pos]
                        if snp_name not in self.gold[ind]:
                            unranked_list.append([score,False,ind,snp_name,chrom,pos,genos,None])
                        elif genos == self.gold[ind][snp_name]['for']:
                            unranked_list.append([score,True,ind,snp_name,chrom,pos,genos,self.gold[ind][snp_name]])
                        else:
                            unranked_list.append([score,False,ind,snp_name,chrom,pos,genos,self.gold[ind][snp_name]])
        unranked_list.sort(key = lambda l: l[0],reverse=True)
        return(unranked_list)
                        
                        
    def precision(self,ranked_list):
        return(len([i for i in ranked_list if i[1] == True])/len(ranked_list))

    def recall(self,ranked_list):
        return(len([i for i in ranked_list if i[1] == True])/self.num_gold)

    def print_curve(self,relevent):
        print("precision","recall")
        for i in range(1,len(relevent)):
            print('{},{}'.format(self.precision(relevent[0:i]),self.recall(relevent[0:i])))

