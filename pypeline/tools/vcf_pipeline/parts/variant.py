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

from pypeline.node import CommandNode
from pypeline.atomiccmd.command import AtomicCmd
from pypeline.atomiccmd.builder import AtomicJavaCmdBuilder
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

class UnifiedGenotyperNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infiles, outfile, options, dependencies = ()):
        infiles = safe_coerce_to_tuple(infiles)
        jar_file = os.path.join(options.jar_root,"GenomeAnalysisTK.jar")
        UnifiedGenotyper = AtomicJavaCmdBuilder(options,jar_file)
        UnifiedGenotyper.set_option("-R", "%(IN_REFERENCE)s")
        UnifiedGenotyper.set_option("-T", "UnifiedGenotyper")
        for bam in infiles:
            UnifiedGenotyper.add_option("-I", bam)
        UnifiedGenotyper.set_option("-o", "%(OUT_VCFFILES)s")
        UnifiedGenotyper.set_option("-stand_call_conf", "50.0")
        UnifiedGenotyper.set_option("-stand_emit_conf", "10.0")
        UnifiedGenotyper.set_option("-dcov", "200")

        UnifiedGenotyper.set_kwargs(
            IN_REFERENCE = reference,
            OUT_VCFFILES = outfile
            OUT_VCF_IDX  = outfile + "idx"
        )

        return {
            "commands" : {
                "unifiedgenotyper" : UnifiedGenotyper
            }
        }
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands['unifiedgenotyper'].finalize() ]
        description = "<UnifiedGenotyper: %s -> %s" % ( "\n".join(parameters.infiles), parameters.outfile )

        CommandNode.__init__(self,
                             description = description,
                             command = ParallelCmds(commands),
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
        bcftools.set_option('-b')
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
        description = "<VariantCaller : '%s' -> %s" %( "".join(parameters.infiles),
                                                       parameters.outfile)
        CommandNode.__init__(self,
                             description  = description,
                             command      = ParallelCmds(commands),
                             dependencies = parameters.dependencies)


def build_variant_nodes(options,reference, group, dependencies = ()):
    gatk_outfile = os.path.join(options.destination,"gatk.%s" % (group['Group']) + ".raw.vcf") 
    gatk_variants = UnifiedGenotyperNode.customize(
        reference = reference,
        infiles = group['Bams'],
        outfile = gatk_outfile,
        options = options
    )

    samtools_outfile = os.path.join(options.destination,"samtools.%s" % (group['Group']) + ".raw.vcf") 
    samtools_variants = VariantNode.customize(
        reference = reference,
        infiles = group['Bams'],
        outfile = samtools_outfile,
        options = options
    )
    samtools_variants = samtools_variants.build_node()
    gatk_variants = gatk_variants.build_node()
    
    return gatk_variants


def chain(pipeline, options, makefiles):
    destination = options.destination
    nodes = []
    for makefile in makefiles:
        for prefix in makefile['Prefixes']:
            for group in makefile['Targets']:
                nodes.append(
                    build_variant_nodes(
                        options,
                        makefile['Prefixes'][prefix]['Path'],
                        group
                    )
                )
    return nodes
            
