#!/usr/bin/python

class vcf_merge(object):
    def __init__(self):
        self.output_file = "merged.vcf"
        self.header = {}
        self.vars = []

    def set_output_file(self,output_file):
        self.output_file = outpuf_file

    def read_vcf(self,vcf_file):

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i','--input_vcf',type=str,action='append',help="Input VCF files to merge. Multiple VCF files accepted.")
    parser.add_option('-o','--output',type=str,help="Out file name")
    options,args = parser.parse_arge(sys.argv[1:])

    merged = vcf_merge()
    merged.set_output(options.output)
    for vcf in options.input_vcf:
        merged.read_vcf(vcf)
