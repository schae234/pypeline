#!/usr/bin/python
#
# Copyright (c) 2012 Robert Schaefer <schae234@umn.edu> and Mikkel Schubert <MSchubert@snm.ku.dk>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import glob

from pypeline.node import CommandNode, MetaNode
from pypeline.atomiccmd.command import AtomicCmd
from pypeline.atomiccmd.builder import AtomicJavaCmdBuilder,AtomicJava7CmdBuilder
from pypeline.atomiccmd.sets import ParallelCmds
from pypeline.atomiccmd.builder import \
     AtomicCmdBuilder, \
     use_customizable_cli_parameters, \
     create_customizable_cli_parameters

from pypeline.nodes.samtools import GenotypeNode, TabixIndexNode, FastaIndexNode, MPileupNode

import pypeline.common.versions as versions
from pypeline.common.utilities import safe_coerce_to_tuple

SAMTOOLS_VERSION = versions.Requirement(
    call   = ("samtools",),
    search = b"Version: (\d+)\.(\d+)\.(\d+)",
    checks = versions.GE(0, 1, 18)
)

class SnpListNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, groups, prefix, options, dependencies = ()):
        # Merge the VCF files
        merge_vcf = AtomicCmdBuilder(['vcf_merge'], OUT_VCF = "merged.vcf")
        for group in groups:
            vcf_file = os.path.join(options.makefile['RecalDir'],
                'gatk.{}.{}.raw.recal_final.vcf'.format(group,prefix)
            )
            merge_vcf.add_option("-i",vcf_file)
        merge_vcf.add_option("-o", '%(OUT_VCF)s')
    

        # Create the snp list
        snp_list = AtomicCmdBuilder(['vcf_snp_list'])
        snp_list.add_option('--recal_dir',options.makefile['RecalDir'])
        snp_list.add_option('')
        return {
            'commands' : {
                'merge' : merge_vcf,
                'Snp' : snp_list
            }
        }

    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['Snp'].finalize()]
        description = "<SNP List Generator Node>"
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies
        )

class ApplyRecalibrationNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infile, options, dependencies = ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
        apply_recal = AtomicJava7CmdBuilder(options,jar_file)
        apply_recal.add_option("-T","ApplyRecalibration")
        apply_recal.set_option("-R","%(IN_REFERENCE)s")
        apply_recal.set_option("-input","%(IN_VCF)s")
        apply_recal.add_option("-mode","SNP")
        #apply_recal.add_option("--ts_filter_level","99.0")
        apply_recal.add_option("--lodCutoff","0")
        apply_recal.set_option("-recalFile","%(IN_RECAL)s")
        apply_recal.set_option("-tranchesFile","%(IN_TRANCHES)s")
        apply_recal.set_option("-o","%(OUT_RECAL)s")
        apply_recal.set_kwargs(
            IN_REFERENCE = reference,
            IN_VCF = infile,
            IN_RECAL = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",".recal")),
            IN_TRANCHES = os.path.join(options.makefile['RecalDir'],
               os.path.basename(infile).replace(".vcf",".tranches")),
            OUT_RECAL = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",".recal_final.vcf")),
            OUT_IDX = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",".recal_final.vcf.idx")),
        )
        return {
            'commands' : {
                'apply_recal' : apply_recal
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['apply_recal'].finalize()]
        description = "<Variant Apply Recal: {}".format(os.path.basename(parameters.infile))
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies
        )

class VariantFilterNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infile, outfile, filters, options, dependencies = ()):
        # filter reads
        percentile = str(options.makefile['vcf_percentile_threshold'])
        flt = AtomicCmdBuilder(['vcf_qual_percentile'],
            IN_VCF = infile,
            OUT_VCF = infile.replace(".raw.vcf",".gatk_samtools_intersect.vcf")
        )
        if options.makefile['union_vcf']:
            union_file = infile.replace(
                    options.makefile['union_vcf']['replace'],
                    options.makefile['union_vcf']['with']
            )
        flt.set_option('--union_vcf',union_file)
        flt.set_option('-o','%(OUT_VCF)s')
        flt.add_option(infile)
        return {
            'commands':{
                'Filter': flt
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['Filter'].finalize()]
        description = "<Variant Filter: {}".format(os.path.basename(parameters.infile))
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies)

class VariantRecalibratorNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infile, options, dependencies = ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK.jar")
        percentile = str(options.makefile['vcf_percentile_threshold'])
        VariantRecal = AtomicJavaCmdBuilder(options,jar_file)
        VariantRecal.set_option("-T","VariantRecalibrator")
        VariantRecal.set_option("-R","%(IN_REFERENCE)s")
        VariantRecal.set_option("-input","%(IN_VCF)s")
        VariantRecal.add_option('-resource:thresh,known=false,training=true,truth=true,prior=15.0',"%(IN_FLT)s")
        VariantRecal.add_option("-an","DP")
        VariantRecal.add_option("-an","QD")
        VariantRecal.add_option("-an","FS")
        VariantRecal.add_option("-an","MQRankSum")
        VariantRecal.add_option("-an","ReadPosRankSum")
        VariantRecal.set_option("-mode","SNP")
        VariantRecal.add_option("-tranche","100.0")       
        VariantRecal.add_option("-tranche","99.9")       
        VariantRecal.add_option("-tranche","99.0")       
        VariantRecal.add_option("-tranche","90.0")       
        VariantRecal.set_option('-recalFile',"%(OUT_RECAL)s")
        VariantRecal.set_option('-tranchesFile',"%(OUT_TRANCHES)s")
        VariantRecal.set_option('-rscriptFile',"%(OUT_RSCRIPT)s")
 
        VariantRecal.set_kwargs(
            IN_REFERENCE = reference,
            IN_VCF = infile,
            IN_FLT = infile.replace("raw.vcf","raw_p"+percentile+".vcf"),
            OUT_RECAL    = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",'.recal')),
            OUT_TRANCHES = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace('.vcf','.tranches')),
            OUT_RSCRIPT  = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace('.vcf','.R')),
            OUT_IDX      = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",".recal.idx")),
            OUT_RPDF     = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",'.R.pdf')),
            OUT_TPDF     = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",'.tranches.pdf'))
        )

        return {
            'commands' : {
                'VariantRecal' : VariantRecal
            }
        }

    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['VariantRecal'].finalize()]
        description = "<Variant Recalibrator: {}".format(os.path.basename(parameters.infile))
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies)

class UnifiedGenotyperNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infiles, outfile, options, dependencies = ()):
        infiles = safe_coerce_to_tuple(infiles)
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK.jar")
        UnifiedGenotyper = AtomicJavaCmdBuilder(options,jar_file)
        UnifiedGenotyper.set_option("-R", "%(IN_REFERENCE)s")
        UnifiedGenotyper.set_option("-T", "UnifiedGenotyper")
        for bam in infiles:
            assert os.path.exists(bam), "Couldn't find input BAM: {}".format(bam)
            UnifiedGenotyper.add_option("-I", bam)
        UnifiedGenotyper.set_option("-o", "%(OUT_VCFFILES)s")
        UnifiedGenotyper.set_option("-stand_call_conf", "30.0")
        UnifiedGenotyper.set_option("-stand_emit_conf", "10.0")
        UnifiedGenotyper.set_option("-dcov", "200")
        UnifiedGenotyper.set_option("-nct", "3")

        UnifiedGenotyper.set_kwargs(
            IN_REFERENCE = reference,
            OUT_VCFFILES = outfile,
            OUT_VCF_IDX  = outfile + ".idx"
        )

        return {
            "commands" : {
                "unifiedgenotyper" : UnifiedGenotyper
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['unifiedgenotyper'].finalize() ]
        description = "<UnifiedGenotyper: {}".format(os.path.basename( parameters.outfile))

        CommandNode.__init__(self,
                             description = description,
                             command = ParallelCmds(commands),
                             dependencies = parameters.dependencies)

class VariantMergeNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, vcf_list, reference, options, dependencies= ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
        merge = AtomicJava7CmdBuilder(options, jar_file) 
        merge.add_option('-T','CombineVariants')
        merge.set_option('-R',"%(IN_REFERENCE)s")
        merge.set_option('-nt','4')
        merge.set_option('--combineAnnotations')
        for vcf in vcf_list:
            merge.add_option("--variant",vcf)
        merge.add_option("-o",'%(OUT_MERGE)s')
        merge.set_kwargs(
            IN_REFERENCE = reference,
            OUT_MERGE = os.path.join(options.makefile['OutDir'],"MERGED.vcf"),
            OUT_IDX = os.path.join(options.makefile['OutDir'],"MERGED.vcf.idx")
        )
        return {
            'commands' : {
                'merge' : merge
            }
        }
        
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['merge'].finalize()]
        description = "<Variant Merge Node"
        CommandNode.__init__(self,
                             description  = description,
                             command      = ParallelCmds(commands),
                             dependencies = parameters.dependencies)


class VariantNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infiles, outfile, options, dependencies= ()):
        assert outfile.lower().endswith('.vcf')
       
        # Create the pileup command 
        pileup = AtomicCmdBuilder(
            ['samtools','mpileup'],
            IN_REFERENCE = reference,
            OUT_STDOUT   = AtomicCmd.PIPE,
            CHECK_SAM    = SAMTOOLS_VERSION
        )
        pileup.set_option('-u') # uncompressed output
        pileup.set_option('-f', "%(IN_REFERENCE)s") # Add reference option

        
        for bam in infiles:
            pileup.add_option(bam)

        # Create variant caller command
        bcftools = AtomicCmdBuilder(
                ['bcftools','view'],
                IN_STDIN = pileup,
                OUT_STDOUT = outfile
        )
        bcftools.set_option('-v')
        bcftools.set_option('-c')
        bcftools.set_option('-g')
        bcftools.set_option('-')

        return {
            "commands" : {
                "pileup" : pileup,
                "bcftools" : bcftools, 
            }
        }

    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands[key].finalize() for key in ('pileup','bcftools')]
        description = "<Samtools VariantCaller : {}".format(os.path.basename(parameters.outfile))
        CommandNode.__init__(self,
                             description  = description,
                             command      = ParallelCmds(commands),
                             dependencies = parameters.dependencies)


def build_variant_nodes(options,reference, group, dependencies = ()):
    gatk_outfile = os.path.join(options.makefile['OutDir'],"gatk.%s.%s" % (group['Group'],reference['Label']) + ".raw.vcf") 
    # Build the Variant Calling Nodes
    gatk_variants = UnifiedGenotyperNode.customize(
        reference = reference['Path'],
        infiles = [	os.path.join(options.makefile['BaseDir'],
			ind + "."+ reference['Label'] + ".realigned.bam") 
			for ind in group['Inds']],
        outfile = gatk_outfile,
        options = options
    )

    samtools_outfile = os.path.join(options.makefile['OutDir'],"samtools.%s.%s" % (group['Group'],reference['Label']) + ".raw.vcf") 
    samtools_variants = VariantNode.customize(
        reference = reference['Path'],
        infiles = [     os.path.join(options.makefile['BaseDir'],
			ind + "."+ reference['Label'] + ".realigned.bam") 
			for ind in group['Inds']],
        outfile = samtools_outfile,
        options = options
    )
    samtools_variants = samtools_variants.build_node()
    gatk_variants = gatk_variants.build_node()
 
    # Build the Variant Filtering Nodes
    gatk_filtered = VariantFilterNode.customize(
        reference = reference['Path'],
        infile = gatk_outfile,
        outfile = gatk_outfile.replace(".raw.vcf","gatk_samtools_intersect.vcf"),
        filters = {
            "--union_vcf" : infile.replace(
                options.makefile['union_vcf']['replace'],
                options.makefile['union_vcf']['with']
            ),
            ""
        }
        options = options,
        dependencies = [gatk_variants,samtools_variants]
    )
    gatk_filtered = gatk_filtered.build_node()

  

    return MetaNode(description = "Variant Recalbibration",
                dependencies = [gatk_filtered]
    )
def build_merge_node(groups,prefix,options,dependencies = ()):
 
    # Find the samtools and gatk intersect files
    intersect_files = glob.glob(
        os.path.join(options.makefile['OutDir'],"*gatk_samtools_intersect*")
    )
   
    intersect_merge = VariantMergeNode.customize(
        vcf_list = intersect_files, 
        reference = prefix['Path'], 
        options = options, 
        dependencies = dependencies
    )
    intersect_merge = intersect_merge.build_node()

    intersect_threshold = Vari

    return MetaNode(description = "SNP Merge node",
        dependencies = [intersect_merge]
    )
    
def build_recalibration_nodes(group,reference,options,dependencies = ()):
    gatk_outfile = os.path.join(
        options.makefile['OutDir'],"gatk.%s.%s" % (group['Group'],reference['Label']) + ".raw.vcf"
    ) 
    # Build the 

    # Build the Recalibration Nodes
    gatk_recal = VariantRecalibratorNode.customize(
            reference = reference['Path'],
            infile = gatk_outfile,
            options = options,
            dependencies = [gatk_filtered]
    )
    gatk_recal = gatk_recal.build_node()

    # Build the REcalibration Application nodes
    gatk_apply = ApplyRecalibrationNode.customize(
            reference = reference['Path'],
            infile = gatk_outfile,
            options = options,
            dependencies = [gatk_recal]
    )
    gatk_apply = gatk_apply.build_node()


def chain(pipeline, options, makefiles):
    nodes = []
    for makefile in makefiles:
	options.makefile = makefile['Options']
        for prefix in makefile['Prefixes']:
            # Call variants with both samtools and gatk
            # Create filtes containing only intersection b/w callers
            for group in makefile['Targets']:
                nodes.append(
                    build_variant_nodes(
            			options,
                        makefile['Prefixes'][prefix],
                        group
                    )
                )
            # Here we have intersections between gatk and samtools
            # merge them so we can choose variants from multiple calling groups
            groups = [i['Group'] for i in makefile['Targets']]
            nodes.append(build_snp_list_node(
                groups,
                makefile['Prefixes'][prefix],
                options,
                nodes
            ))
            # Build recalibration nodes using two classes of nodes
            # known snps as well as snps that occur in 
            for group in makefile['Targets']:
                nodes.append(
                    build_recalibration_nodes(
                        group,
                        makefile['Prefixes'][prefix],
                        options
                    )
                )
    return nodes
            
