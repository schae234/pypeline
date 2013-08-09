#!/usr/bin/python
#
# Copyright (c) 2013 Rob Schaefer <schae234@umn.edu>
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
from pypeline.atomiccmd.command import AtomicCmd
from pypeline.atomiccmd.sets import ParallelCmds
from pypeline.atomiccmd.builder import \
     create_customizable_cli_parameters, \
     use_customizable_cli_parameters, \
     AtomicCmdBuilder, \
     apply_options

from pypeline.node import MetaNode, CommandNode

class fastqDumpNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(self,in_sra, outfile, dependencies = ()):
        fastq_dump = AtomicCmdBuilder(['fastq-dump', "%(IN_SRA)s"],
                                        IN_SRA = in_sra,
                                        OUT_STDOUT = outfile)
    return {"commands" : {"fastq_dump" : fastq_dump}}
    @use_customizable_cli_parameters
    def __init__(self, parameters):
        commands = [parameters.commands[key].finalize() for key in ("fastq_dump",)]
        description = "<FastqDump: {} -> {}>".format(in_sra, outfile)
        CommandNode.__init__(   
            self, description = description,
            command = ParallelCmds(commands),
            dependecies = parameters.dependencies)

class catNode(CommandNode):
    @create_customizalbe_cli_parameters
    def customize(self, infile, dependencies = ())
        cat = AtomicCmdBuilder(['cat','%(IN_FILE)s'])
    def __init__(self):
        CommandNode.__init__(self,
            description="Cat Node",
            command = AtomicCmd()
        )

class RunNode(MetaNode):
    def __init__(self,accession = "TBD", infile = ""):
        self.accession = accession
        self.infile = infile
        MetaNode.__init__(description = "Run Node")

    def fastq_dump(self):
        dmp = fastqDumpNode.customize(self.infile, )
