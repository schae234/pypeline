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
    def customize(cls, reference, infile, options, model_name, dependencies = ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
        apply_recal = AtomicJava7CmdBuilder(options,jar_file)
        apply_recal.add_option("-T","ApplyRecalibration")
        apply_recal.set_option("-R","%(IN_REFERENCE)s")
        apply_recal.set_option("-input","%(IN_VCF)s")
        apply_recal.add_option("-mode","SNP")
        apply_recal.add_option("--lodCutoff","0")
        apply_recal.set_option("-recalFile","%(IN_RECAL)s")
        apply_recal.set_option("-tranchesFile","%(IN_TRANCHES)s")
        apply_recal.set_option("-o","%(OUT_RECAL)s")
        apply_recal.set_kwargs(
            IN_REFERENCE = reference,
            IN_VCF = infile,
            IN_RECAL = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",model_name+".recal")),
            IN_TRANCHES = os.path.join(options.makefile['RecalDir'],
               os.path.basename(infile).replace(".vcf",model_name+".tranches")),
            OUT_RECAL = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",model_name+".recal_final.vcf")),
            OUT_IDX = os.path.join(options.makefile['RecalDir'],
                os.path.basename(infile).replace(".vcf",model_name+".recal_final.vcf.idx")),
        )
        return {
            'commands' : {
                'apply_recal' : apply_recal
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['apply_recal'].finalize()]
        description = "<Variant Apply Recal: {}".format(os.path.basename(parameters.model_name))
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies
        )

class VariantVCFToolsNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls,infile,outfile,options,dependencies= ()):
        vcftools = AtomicCmdBuilder(['vcftools']
            IN_VCF = infile
            OUT_VCF = outfile
        )
        vcftools.set_option('--vcf','%(IN_VCF)s')
        vcftools.set_option('--out','%(OUT_VCF)s')
    

    @use_customizable_cli_parameters
    def __init__(self,parameters):
        pass

class VariantFilterNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infile, outfile, filters, options, dependencies = ()):
        # filter reads
        percentile = str(options.makefile['vcf_percentile_threshold'])
        flt = AtomicCmdBuilder(['vcf_qual_percentile'],
            IN_VCF = infile,
            OUT_VCF = outfile
        )
        for key,val in filters.items():
            flt.add_option(key,val)
        flt.set_option('--out','%(OUT_VCF)s')
        flt.add_option(infile)
        return {
            'commands':{
                'Filter': flt
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['Filter'].finalize()]
        description = "<Variant Filter: {}".format(os.path.basename(parameters.outfile))
        CommandNode.__init__(self,
            description = description,
            command = ParallelCmds(commands),
            dependencies = parameters.dependencies)

class VariantRecalibratorNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infile, recal_files, options, model_name, dependencies = ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
        VariantRecal = AtomicJava7CmdBuilder(options,jar_file)
        VariantRecal.set_option("-T","VariantRecalibrator")
        VariantRecal.set_option("-R","%(IN_REFERENCE)s")
        VariantRecal.set_option("-input","%(IN_VCF)s")
        for i,res in enumerate(recal_files):
            VariantRecal.add_option(
                '-resource:{},known={},training={},truth={},prior={}'.format(
                    res['resource'], res['known'],
                    res['training'], res['truth'],res['prior']
                ),
                '%(IN_REC{})s'.format(i)
            )
        #VariantRecal.add_option("-an","DP")
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
            OUT_RECAL    = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",model_name+'.recal')),
            OUT_TRANCHES = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace('.vcf',model_name+'.tranches')),
            OUT_RSCRIPT  = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace('.vcf',model_name+'.R')),
            OUT_IDX      = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",model_name+".recal.idx")),
            OUT_RPDF     = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",model_name+'.R.pdf')),
            OUT_TPDF     = os.path.join(options.makefile['RecalDir'],
                 os.path.basename(infile).replace(".vcf",model_name+'.tranches.pdf'))
        )
        for i,res in enumerate(recal_files):
            VariantRecal.add_kwarg("IN_REC{}".format(i),res['vcf'])

        return {
            'commands' : {
                'VariantRecal' : VariantRecal
            }
        }

    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['VariantRecal'].finalize()]
        description = "<Variant Recalibrator: {}".format(os.path.basename(parameters.model_name))
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
        #UnifiedGenotyper.set_option("-nct", "3")
        UnifiedGenotyper.set_option("-L", "chrUn2:1-19213991")
    

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
    def customize(cls, vcf_list,outfile, reference, options, dependencies= ()):
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
        merge = AtomicJava7CmdBuilder(options, jar_file,
            IN_REFERENCE = reference,
            OUT_MERGE = os.path.join(outfile),
            OUT_IDX = os.path.join(outfile+".idx")
        ) 
        merge.add_option('-T','CombineVariants')
        merge.set_option('-R',"%(IN_REFERENCE)s")
        merge.set_option('-nt','4')
        merge.set_option('--combineAnnotations')
        for vcf in vcf_list:
            merge.add_option("--variant",vcf)
        merge.add_option("-o",'%(OUT_MERGE)s')
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

#class VariantAnnotateNode(CommandNode):
#   @create_customizable_cli_parameters
#   def customize(cls,infile,outfile,bam_list,referecnce,options,dependencies = ()):
#       jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK-2.8-1.jar")
#       annotate = AtomicJava7CmdBuilder(options,jar_file,
#           IN_REFERENCE = reference,
#           OUT_ANNOTATED = os.path.join(outfile),
#           OUT_IDX = os.path.join(outfile+".idx")
#       )
#       annotate.add_option('-T','VariantAnnotator')
#       annotate.add_option('-R','%(IN_REFERENCE)s')
#       annotate.add_option('-nt','4')



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
        pileup.set_option('-r','chrUn2:1-19214051')
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

def PRNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls,final_report,map_file,options, dependencies=()):
        pass

    @use_customizable_cli_parameters
    def __init__(self,parameters):
        pass
        

def build_variant_nodes(options,reference, group, dependencies = ()):
    gatk_outfile = os.path.join(
        options.makefile['OutDir'],"gatk.{}.{}.raw.vcf".format(
            group['Group'],reference['Label'])
    ) 
    # Build the GATK Variant Calling Node
    gatk_variants = UnifiedGenotyperNode.customize(
        reference = reference['Path'],
        infiles = [	os.path.join(options.makefile['BaseDir'],
			ind + "."+ reference['Label'] + ".realigned.bam") 
			for ind in group['Inds']],
        outfile = gatk_outfile,
        options = options
    )

    # Build the SAMTOOLs Variant Calling Node
    samtools_outfile = os.path.join(options.makefile['OutDir'],
        "samtools.{}.{}.raw.vcf".format(
        group['Group'],reference['Label'])
    ) 
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
 
    # Find the intersect between samtools and GATK
    union_variants = VariantFilterNode.customize(
        reference = reference['Path'],
        infile = gatk_outfile,
        outfile = os.path.join(
            options.makefile['OutDir'],
            gatk_outfile.replace(".raw.vcf",".gatk_samtools_intersect.vcf")
        ),
        filters = {
            "--intersect_vcf" : gatk_outfile.replace(
                options.makefile['intersect_vcf']['replace'],
                options.makefile['intersect_vcf']['with']
            ),
            "--emit": "pass"
        },
        options = options,
        dependencies = [gatk_variants,samtools_variants]
    )
    union_variants = union_variants.build_node()

    return MetaNode(description = "Variant Recalbibration",
                dependencies = [union_variants]
    )

def build_merge_node(groups,prefix,options,dependencies = ()):
    # Find the samtools and gatk intersect files
    intersect_files = glob.glob(
        os.path.join(options.makefile['OutDir'],
            '*.{}.{}.vcf'.format(
                prefix['Label'],
                "gatk_samtools_intersect"
            )
        )
    )
  
#   gatk_merge = VariantMergeNode.customize(
#       vcf_list = glob.glob(os.path.join(options.makefile['OutDir'],"gatk*Un.raw.vcf")), 
#       outfile = os.path.join(options.makefile['OutDir'],"MERGED_GATK.vcf"),
#       reference = prefix['Path'], 
#       options = options, 
#       dependencies = dependencies
#   )
#   gatk_merge = gatk_merge.build_node()
#   samtools_merge = VariantMergeNode.customize(
#       vcf_list = glob.glob(os.path.join(options.makefile['OutDir'],"samtools*Un.raw.vcf")), 
#       outfile = os.path.join(options.makefile['OutDir'],"MERGED_SAMTOOLS.vcf"),
#       reference = prefix['Path'], 
#       options = options, 
#       dependencies = dependencies
#   )
#   samtools_merge = samtools_merge.build_node()
 
    intersect_merge = VariantMergeNode.customize(
        vcf_list = intersect_files, 
        outfile = os.path.join(options.makefile['OutDir'],
            "MERGED.{}.vcf".format(prefix['Label'])
        ),
        reference = prefix['Path'], 
        options = options, 
        dependencies = dependencies
    )
    intersect_merge = intersect_merge.build_node()


#   annotate_merged = VariantAnnotateNode.customize(
#       infile = os.path.join(options.makefile['OutDir'],
#           "MERGED.{}.vcf".format(prefix['Label'])
#       ),
#       outfile = os.path.join(options.makefile['OutDir'],
#           "MERGED.{}.annotated.vcf".format(prefix['Label'])
#       ),
#       reference = prefix['Path'], 
#       options = options, 
#       dependencies = dependencies
#   )
#   annotate_merged = annotate_merged.build_node()

#   intersect_qual = VariantFilterNode.customize(
#    reference = prefix['Path'],
#       infile = os.path.join(options.makefile['OutDir'],
#           "MERGED.{}.vcf".format(prefix['Label'])
#       ),
#       outfile = os.path.join(options.makefile['OutDir'],
#           "MERGED_QUAL.{}.vcf".format(prefix['Label'])
#       ),
#       filters = {
#           "--percentile" : options.makefile['vcf_percentile_threshold'],
#           "--skip_chrom" : "chr1"
#       },
#       options = options,
#       dependencies = dependencies + [intersect_merge]
#   )
#   intersect_qual = intersect_qual.build_node()

#   # Create a filterd VCF containing only 54K snps on CH1
#   intersect_CH1_map_file = VariantFilterNode.customize(
#       reference = prefix['Path'],
#       infile = os.path.join(options.makefile['OutDir'],
#           "MERGED.{}.vcf".format(prefix['Label'])
#       ),
#       outfile = os.path.join(options.makefile['OutDir'],
#           "MERGED_CH1_SNP_LIST.{}.vcf".format(prefix['Label'])
#       ),
#       filters = {
#           "--map_file" : options.makefile['map_file'],
#           "--keep_chrom" : "chr1"
#       },
#       options = options,
#       dependencies = dependencies + [intersect_merge]
#   )
#   intersect_CH1_map_file = intersect_CH1_map_file.build_node()

#   # Create a filtered VCF containing only 54K snps on not CHR1 
#   intersect_map_file = VariantFilterNode.customize(
#       reference = prefix['Path'],
#       infile = os.path.join(options.makefile['OutDir'],"MERGED.vcf"),
#       outfile = os.path.join(options.makefile['OutDir'],"MERGED_SNP_LIST.vcf"),
#       filters = {
#           "--map_file" : options.makefile['map_file'],
#           "--skip_chrom" : "chr1"
#       },
#       options = options,
#       dependencies = dependencies + [intersect_merge]
#   )
#   intersect_map_file = intersect_map_file.build_node()
    
    # Create a filtered VCF containing only 4+ call groups 
    intersect_thresh = VariantFilterNode.customize(
        reference = prefix['Path'],
        infile = os.path.join(options.makefile['OutDir'],
            "MERGED.{}.vcf".format("Equus_cab_nucl_wChrUn")),
        outfile = os.path.join(options.makefile['OutDir'],
            "MERGED_THRESH.{}.vcf".format("Equus_cab_nucl_wChrUn")),
        filters = {
            "--num_call_sets" : options.makefile['num_call_sets'],
            "--skip_chrom" : "chr1",
            "--percentile" : options.makefile['vcf_percentile_threshold'],
            "--emit" : "pass"
        },
        options = options,
        dependencies = dependencies + [intersect_merge]
    )
    intersect_thresh = intersect_thresh.build_node()

    return MetaNode(description = "SNP Merge node",
        dependencies = [ #intersect_map_file, 
                          intersect_thresh,
                         #intersect_qual,
                         #intersect_CH1_map_file,
                         #samtools_merge,
                         #gatk_merge
                          intersect_merge
                         ]
    )
    
def build_recalibration_node(group,reference,options,dependencies = ()):
    gatk_outfile = os.path.join(
        options.makefile['OutDir'],"gatk.{}.{}.gatk_samtools_intersect.vcf".format(
            group['Group'],
            reference['Label'])
    ) 
    
#   ########
#   # Build the QUAL thresh model
#   qual_thresh = VariantRecalibratorNode.customize(
#           reference = reference['Path'],
#           infile = gatk_outfile,
#            recal_files = [
#               {
#                   'resource':'QUAL',
#                   'known':'false',
#                   'training': "true",
#                   'truth' : "true",
#                   'prior' : '12.0',
#                   'vcf':os.path.join(options.makefile['OutDir'],"MERGED_QUAL.vcf"),
#               },
#               {
#                   'resource':'CH1',
#                   'known':'true',
#                   'training': "false",
#                   'truth' : "false",
#                   'prior' : '2.0',
#                   'vcf':os.path.join(options.makefile['OutDir'],"MERGED_CH1_SNP_LIST.vcf"),
#               }
#           ],
#           options = options,
#           model_name = 'qual_thresh2',
#           dependencies = dependencies
#   )
#   qual_thresh = qual_thresh.build_node()

#   ########
#   # Build the SNP and Merge Model
#   snp_merge = VariantRecalibratorNode.customize(
#           reference = reference['Path'],
#           infile = gatk_outfile,
#           recal_files = [
#               {
#                   'resource':'snp',
#                   'known':'false',
#                   'training': "true",
#                   'truth' : "true",
#                   'prior' : '12.0',
#                   'vcf':os.path.join(options.makefile['OutDir'],"MERGED_SNP_LIST.vcf"),
#               },
#               {
#                   'resource':'thresh',
#                   'known':'false',
#                   'training': "true",
#                   'truth' : "false",
#                   'prior' : '10.0',
#                   'vcf':os.path.join(options.makefile['OutDir'],"MERGED_THRESH.vcf"),
#                }
#           ],
#           options = options,
#           model_name = 'snp_and_thresh',
#           dependencies = dependencies
#   )
#   snp_merge = snp_merge.build_node()

    ########
    # Build 4+ Group Only Model
    group_only = VariantRecalibratorNode.customize(
            reference = reference['Path'],
            infile = gatk_outfile,
            recal_files = [
                {
                    'resource':'thresh',
                    'known':'false',
                    'training': "true",
                    'truth' : "true",
                    'prior' : '12.0',
                    'vcf':os.path.join(options.makefile['OutDir'],
                        "MERGED_THRESH.Equus_cab_nucl_wChrUn.vcf"
                    ),
                 }
            ],
            options = options,
            model_name = 'group_only',
            dependencies = dependencies
    )
    group_only = group_only.build_node()

   #########
   ## Build the SNP ONLY Model
   #snp_only = VariantRecalibratorNode.customize(
   #        reference = reference['Path'],
   #        infile = gatk_outfile,
   #        recal_files = [
   #            {
   #                'resource':'snp',
   #                'known':'false',
   #                'training': "true",
   #                'truth' : "true",
   #                'prior' : '12.0',
   #                'vcf':os.path.join(options.makefile['OutDir'],"MERGED_SNP_LIST.vcf"),
   #            },
   #        ],
   #        options = options,
   #        model_name = 'snp_only',
   #        dependencies = dependencies
   #)
   #snp_only = snp_only.build_node()

    # Build the REcalibration Application nodes
    go_apply = ApplyRecalibrationNode.customize(
            reference = reference['Path'],
            infile = gatk_outfile,
            options = options,
            model_name = 'group_only',
            dependencies = group_only
    )
    go_apply = go_apply.build_node()


   ## Build the REcalibration Application nodes
   #so_apply = ApplyRecalibrationNode.customize(
   #        reference = reference['Path'],
   #        infile = gatk_outfile,
   #        options = options,
   #        model_name = 'snp_only',
   #        dependencies = snp_only
   #)
   #so_apply = so_apply.build_node()


   ## Build the REcalibration Application nodes
   #qual_apply = ApplyRecalibrationNode.customize(
   #        reference = reference['Path'],
   #        infile = gatk_outfile,
   #        options = options,
   #        model_name = 'qual_thresh2',
   #        dependencies = qual_thresh
   #)
   #qual_apply = qual_apply.build_node()
   

   ## Build the REcalibration Application nodes
   #sm_apply = ApplyRecalibrationNode.customize(
   #        reference = reference['Path'],
   #        infile = gatk_outfile,
   #        options = options,
   #        model_name = 'snp_and_thresh',
   #        dependencies = snp_merge
   #)
   #sm_apply = sm_apply.build_node()

   ## Run the PR analysis on the Morgans
   #MOR_PR = PRNode.customize(
   #        final_repoert = os.path.join(
   #            options.makefile['BaseDir'],"000_PR/Minnesota-Anderson\ Equine\ V1\ 19jun2012_FinalReport.txt"
   #        ),
   #        map_file = os.path.join(
   #            options.makefile['BaseDir'],"CH1_Gentrain.map"
   #        ),
   #        options = options,
   #        vcf_files = [

   #        ],
   #        dependencies = [sm_apply,qual_apply]
   #)

    return MetaNode(description="VCF Recal Node",
        #dependencies = [sm_apply,qual_apply,go_apply]
        dependencies = [go_apply]
    )


def build_snp_list(groups,prefix,options,dependencies = ()):
    recal_files = glob.glob(
        os.path.join(options.makefile['RecalDir'],"gatk*group_only*.vcf")
    )
    VQSLOD_cutoff = float(options.makefile['VQSLOD_cutoff'])
    
    recal_merge = VariantMergeNode.customize(
        vcf_list = recal_files,
        outfile = os.path.join(options.makefile['RecalDir'],
            'RECAL_MERGED.{}.vcf'.format(prefix['Label'])
        ),
        reference = prefix['Path'],
        options = options,
        dependencies = dependencies
    )
    recal_merge = recal_merge.build_node()

    recal_filter = VariantFilterNode.customize(
         reference = prefix['Path'],
         infile = os.path.join(options.makefile['RecalDir'],
            'RECAL_MERGED.{}.vcf'.format(prefix['Label'])
         ), 
         outfile = os.path.join(options.makefile['RecalDir'],
             "RECAL_FILTERED.{}.vcf".format(prefix['Label'])
         ),
         filters = {
             "--not_within" :  '20',
             "--allelic" :  '2',
             "--repetitive" : "Repeat_Regions.txt",
             "--emit" : "pass",
             "--field" : 'AC',
             "--thresh" : '2'
         },
         options = options,
         dependencies = dependencies + [recal_merge]
    )
    recal_filter = recal_filter.build_node()

    return MetaNode(description="SNP List Node",
        dependencies = [recal_filter]
    )

def chain(pipeline, options, makefiles):
    nodes = []
    for makefile in makefiles:
	options.makefile = makefile['Options']
        for prefix in makefile['Prefixes']:
            # Call variants with both samtools and gatk
            # Create filtes containing only intersection b/w callers
            variant_nodes = [
                build_variant_nodes(
                    options, 
                    makefile['Prefixes'][prefix],
                    group) for group in makefile['Targets']
            ]
            # Here we have intersections between gatk and samtools
            # merge them so we can choose variants from multiple calling groups
            groups = [i['Group'] for i in makefile['Targets']]
            merge_node = [build_merge_node(
                groups,
                makefile['Prefixes'][prefix],
                options,
                variant_nodes
            )]
            # Build recalibration nodes using two classes of nodes
            # known snps as well as snps that occur in 
            recal_nodes = [
               build_recalibration_node(
                   group,
                   makefile['Prefixes'][prefix],
                   options,
                   merge_node
               ) for group in makefile['Targets']
            ]
            snp_list = [
                build_snp_list(
                groups,
                makefile['Prefixes'][prefix],
                options,
                recal_nodes
                )
            ]
    return variant_nodes + merge_node + recal_nodes + snp_list
            
