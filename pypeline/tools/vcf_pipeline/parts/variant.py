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
    checks = version.GE(0, 1, 18)
)

class VarientNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, reference, infiles = (), outfile, dependencies= ()):
        assert outfile.lower().endswith('.vcf.bgz')
       
        # Create the pileup command 
        pileup = AtomicCmdBuilder(
            ['samtools','mpileup'],
            IN_REFERENCE = reference,
            IN_BAMS      = safe_coerce_to_tuple(infiles),
            OUT_STDOUT   = AtomicCmd.PIPE,
            CHECK_SAM    = SAMTOOLS_VERSION
        )

def build_variant_nodes(reference, bams):
    
    import pdb; pdb.set_trace();
    variants = GenotypeNode.customize(
        reference = reference,
        infile = bams,
        outfile = outfile
    )
    variants = variants.build_node()


def chain(pipeline, options, makefiles):
    destination = options.destination
    for makefile in makefiles:
        nodes = []
        for prefix in makefile['Prefixes']:
            for group in makefile['Targets']:
                nodes.append(
                    build_variant_nodes(
                        makefile['Prefixes'][prefix]['Path'],
                        makefile['Targets'][group]['BAMs']
                    )
                )
            
