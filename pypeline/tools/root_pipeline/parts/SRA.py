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

from pypeline.node import MetaNode
import pypeline.common.versions as versions
from pypeline.tools.root_pipeline.parts.Study import StudyNode


'''
    Build the SRA node based on options and makefiles
'''
class SRANode(MetaNode):
    def __init__(self, accession = "TBD", title = 'Empty Short Read Archive', studies = ()):
        self.title = title
        self.accession = accession
        self.studies = [
            StudyNode(
                title     = study['Title'],
                submitter = study['Submitter'],
                accession = study['Accession'],
                experiments = study['Experiments'])
            for study in studies
        ]
        MetaNode.__init__(self,description = "Short Read Archive Node")
