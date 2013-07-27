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
from pypeline.atomiccmd.sets import ParallelCmds
from pypeline.atomiccmd.builder import \
     AtomicCmdBuilder, \
     use_customizable_cli_parameters, \
     create_customizable_cli_parameters

from pypeline.nodes.samtools import GenotypeNode, TabixIndexNode, FastaIndexNode, MPileupNode

import pypeline.common.versions as versions

SAMTOOLS_VERSION = versions.Requirement(
    call   = ("samtools",),
    search = b"Version: (\d+)\.(\d+)\.(\d+)",
    checks = versions.GE(0, 1, 18)
)

class VariantNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infiles, outfile, dependencies= ()):
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

        bcftools = AtomicCmdBuilder(
                ['bcftools','view'],
                IN_STDIN = pileup,
                OUT_STDOUT = outfile
        )

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
    outfile = os.path.join(options.destination,"variants.%s" % (group['Group']) + ".raw.vcf") 

    variants = VariantNode.customize(
        reference = reference,
        infiles = group['Bams'],
        outfile = outfile
    )
    variants = variants.build_node()
    return variants


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
            
