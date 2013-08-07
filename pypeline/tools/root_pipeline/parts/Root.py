#!/usr/bin/python
#
# Copyright (c) 2012 Mikkel Schubert <MSchubert@snm.ku.dk>
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

import pypeline
import pypeline.ui as ui

from pypeline.node import CommandNode
from pypeline.atomiccmd.command import AtomicCmd
from pypeline.atomiccmd.sets import ParallelCmds
from pypeline.atomiccmd.builder import \
     AtomicCmdBuilder, \
     use_customizable_cli_parameters, \
     create_customizable_cli_parameters


from pypeline.nodes.picard import BuildSequenceDictNode
from pypeline.nodes.samtools import FastaIndexNode, BAMIndexNode

import pypeline.common.versions as versions
from pypeline.tools.root_pipeline.parts.Study import StudyNode

SAMTOOLS_VERSION = versions.Requirement(
    call   = ("samtools",),
    search = b"Version: (\d+)\.(\d+)\.(\d+)",
    checks = versions.GE(0, 1, 18)
)


'''
    The Root node is the (coincidentally) also the root node for the pipeline.
    It keeps track of all the aspects of the project and sub node dependencies.

    It main inputs are configuration parameters and a project makefile. It builds
    everything else based on these parameters.

'''
class RootNode(Node):
    def __init__(self, config, makefile, dependencies = ()):
        # Assign class variables
        self.config = config
        self.makefile = makefile
        self.dependencies = dependencies

        # Process makefile        
        for makefile in makefiles:
            # Append Pipeline Nodes
            
