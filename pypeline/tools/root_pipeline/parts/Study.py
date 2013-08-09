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
from  pypeline.tools.root_pipeline.parts.Experiment import ExperimentNode
from pypeline.node import MetaNode


class StudyNode(MetaNode):
    def __init__(   
            self, title = "Unknown Study", 
            submitter = "Unknown Submitter", 
            accession = "TBD", experiments = ()):
        self.title = title
        self.submitter = submitter
        self.accession = accession
        self.experiments = [
            ExperimentNode(
                title      = exp['Title'],
                accession  = exp['Accession'] ,
                instrument = exp['Instrument'],
                samples    = exp['Samples']
            ) 
            for exp in experiments
        ]
        MetaNode.__init__(self,
            description = "{} Study Node".format(self.title),
            subnodes = self.experiments,
            dependencies = ()
        )
