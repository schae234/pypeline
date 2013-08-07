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

from pypeline.node import Node

import pypeline.common.versions as versions
import pypeline.tools.root_pipeline.makefile as makefile
from pypeline.tools.root_pipeline.parts.SRA import SRANode

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
    def __init__(self, config, optargs, subnodes = (), dependencies = ()):
        Node.__init__(self,
            description = "<Root Node>",
            subnodes = subnodes,
            dependencies = dependencies
        )
        # Assign class variables
        self.config = config
        self.makefiles = makefile.read_makefiles(optargs)
        self.SRAs = []
        self.references = ()
        for m in self.makefiles:
            import pdb; pdb.set_trace()
            self.SRAs.append(SRANode(m['SRA']))
            for ref in m['References']:
                self.references.append(ref)
