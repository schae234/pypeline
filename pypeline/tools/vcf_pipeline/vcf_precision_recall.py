#!/usr/bin/python
from __future__ import print_function,with_statement,division
from optparse import OptionParser
import sys
import re
import os
from collections import defaultdict


class VCF_PR(object):
    verbose = True
    log = sys.stderr

    def __init__(self,map_file,report_file,flt=".*"):
        self.snp_map = defaultdict(dict)
        self.snp_set = set()
        self.gold = defaultdict(dict)
        self.seen = set()
        self.populate_map_file(map_file)
        self.populate_final_report(report_file)

    def populate_map_file(self, map_file,filter='.*'):
        ''' Create mapping between snp id an position '''
        if self.verbose:
            print("Populating Map File",file=self.log)
        with open(map_file,'r') as map_file:
            # compile our filter
            filter = re.compile(filter)
            for line in map_file:
                if not filter.search(line):
                    continue
                chr, id, cm, pos = line.strip().split()
                self.snp_map[id] = (chr,pos)
                self.snp_set.add((chr,pos))
        
    def populate_final_report(self, report_file):
        '''  Read in Final Report  '''
        if self.verbose:
            print("Populating Gold Standard Set",file=self.log)
        with open(report_file,'r') as report:
            while not "[Data]" == report.readline().strip():
                pass
            header = report.readline().strip().split('\t')
            f1_index = header.index('Allele1 - Forward')
            f2_index = header.index('Allele2 - Forward')
            for line in report:
                fields = line.strip().split()
                snp,id,f1,f2,t1,t2,ab1,ab2 = line.strip().split()[0:8]
                if snp not in self.snp_map:
                    #print("{} not id map".format(snp),file=self.log)
                    continue
                self.gold[id][self.snp_map[snp]] = {
                    'for':sorted([fields[f1_index],fields[f2_index]]),
                }

    def relevent(self, vcf_file, rank='VQSLOD',cutoff=None):
        ''' Returns list of ranked Values for T/F '''
        if self.verbose:
            print("Populating Relevent Set",file=self.log)
        unranked_list = list()
        indiv = list()
        self.rank = rank
        with open(vcf_file,'r') as file:
            line_num = 0
            for line in file:
                line_num += 1
                if line.startswith('##'):           # meta dat line
                    continue
                elif line.startswith("#"):          # header line
                    indiv = line.strip().split()[9:]
                    # Reduce the gold standards SNPs to indiv we see here
                    for i in set(self.gold.keys()).difference(indiv):
                        del self.gold[i]
                    if self.verbose:
                        print("Found SNP data for {}".format(",".join(self.gold.keys())),file=self.log)
                else:                                # Variant line
                    fields = line.strip().split()
                    inds = fields[9:]
                    chrom = fields[0].replace('chr','')
                    pos = fields[1]
                    alt = fields[4]
                    ref = fields[3]
                    self.seen.add((chrom,pos))
                    filter = fields[6]
                    if filter == 'LowQual' or (chrom,pos) not in self.snp_set or ',' in alt:
                        continue
                    # Extract the score, QUAL is in a seperate field
                    if rank == 'QUAL':
                        score = float(fields[5])
                    else:
                        rank_field = re.search(str(rank+'=([^;]*)(;?)'),fields[7])
                        if rank_field == None:
                            exit("couldn't find rank on line {}".format(line_num)) 
                        score = float(rank_field.group(1))
                    # Skip scores below the cutoff
                    if cutoff != None and score < float(cutoff):
                        continue
                    for i,ind in enumerate(indiv):
                        # skip indiv not in gold standard
                        if ind not in self.gold:
                            continue
                        genos = inds[i].split(':')[0].replace('0',fields[3]).replace('1',fields[4]).split('/')
                        genos.sort()
                        genos = ''.join(genos)
                        if (chrom,pos) not in self.gold[ind]:
                            pass
                            #unranked_list.append([score,0,ind,chrom,pos,genos,None])
                        elif genos == ''.join(self.gold[ind][chrom,pos]['for']):
                            # True Positive
                            unranked_list.append([score,1,ind,chrom,pos,genos,''.join(self.gold[ind][chrom,pos]['for'])])
                        elif '.' in genos or '-' in self.gold[ind][chrom,pos]['for']:
                            pass
                            # if we didn't make a call for this indiv, dont punish
                            #unranked_list.append([score,0,ind,chrom,pos,genos,None])
                        else:
                            # False positive
                            unranked_list.append([score,-1,ind,chrom,pos,genos,''.join(self.gold[ind][chrom,pos]['for'])])
        if self.verbose:
            print(".....Sorting Ranked List",file=self.log)
        unranked_list.sort(key = lambda l: l[0],reverse=True)
        if self.verbose:
            print("Done",file=self.log)
        return(unranked_list)
                        
                        
    def precision(self,ranked_list):
        true_pos = [i for i in ranked_list if i[1] == 1]
        false_pos = [i for i in ranked_list if i[1] == -1]
        if len(true_pos) == 0 and len(false_pos) == 0:
            return 0
        return(len(true_pos)/(len(true_pos)+len(false_pos)))

    def recall(self,ranked_list,total):
        true_pos = [i for i in ranked_list if i[1] == 1]
        return(len(true_pos)/total)

    def print_curve(self,relevent,header=False,model_name="VQSLOD"):
        if self.verbose:
            print("Calculating Precision Recall for {}".format(model_name),file=self.log)
            print(".... the num of items predicted: {}".format(len(relevent)),file=self.log)
            print(".... the number of snps: {}".format(len(self.snp_set)),file=self.log)
            print(".... percentage of snps seen {}".format((len(self.seen.intersection(self.snp_set))/len(self.snp_set))),file=self.log)
            
        if header:
            print("rank,precision,recall,score,correct,indiv,chrom,pos,emp_geno,ref_geno")
        total = len([i for i in relevent if i[1] == 1])
        for i in range(1,len(relevent)):
            print('{},{},{},{}'.format(
                model_name,
                self.precision(relevent[0:i]),
                self.recall(relevent[0:i],total),
                ','.join(map(str,relevent[i-1]))
            ))
            
def main(argv):
    
    def split_comma(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    parser = OptionParser()
    parser.add_option('-v', '--verbose', default=False, action='store_true')
    parser.add_option('--final_report',default=None, type=str, help='Final Report contain "Gold Standard" variant calls.')
    parser.add_option('--model_names',default='VQSLOD',type=str,action="callback",callback=split_comma,help="provide one model name per vcf file to distinguish in output")
    parser.add_option('--input_vcf',default=None, action="append", type=str,help="input VCF file")
    parser.add_option('--map_file',default=None, type=str,help="PLINK type map file for snp positions")
    parser.add_option('--single_rank', default=None, type=str, action="callback", callback=split_comma, help='comma seperated lists of rankings to be done on the first VCF only')
    parser.add_option('--single_rank_cutoff', default=None, action="callback", callback=split_comma,type=str, help="comma seperated list for cutoffs for ranking, will not assess any variants below this ranking")
    parser.add_option('--rank', type=str, help='ranking field for PR curve')
    parser.add_option('--rank_cutoff', default=0, type=float, help="cutoff for ranking, will not assess any variants below this ranking")
    parser.add_option('--filter', default=".*", type=str, help="filter the gold standard using a regex, e.g. '^chr1'")
    options, args = parser.parse_args(argv)

    if not options.final_report and options.input_vcf and options.map_file:
        raise Exception("Must have all three input files")
    PR = VCF_PR(options.map_file, options.final_report,options.filter)


    for j,vcf in enumerate(options.input_vcf):
       print("Printing PR for {} using {} cutoff at {}".format(os.path.basename(vcf),options.rank,options.rank_cutoff), file=sys.stderr)
       model_name = options.model_names[j]
       rel= PR.relevent(options.input_vcf[j],options.rank,options.rank_cutoff)
       if j == 0:
           PR.print_curve(rel,header=True,model_name=model_name)
       else:
           PR.print_curve(rel,header=False,model_name=model_name)
    if options.single_rank:
        for i,rank in enumerate(options.single_rank):
            print("Printing PR for {} using {} cutoff at {}".format(os.path.basename(options.input_vcf[0]),rank,options.single_rank_cutoff[i]), file=sys.stderr)
            model_name = rank
            rel= PR.relevent(options.input_vcf[0],rank,options.single_rank_cutoff[i])
            PR.print_curve(rel,header=False,model_name=model_name)



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
