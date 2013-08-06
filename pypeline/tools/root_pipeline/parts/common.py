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

from optparse import OptionParser
import pypeline.tools.root_pipeline.makefile
import pypeline.ui as ui


def parse_options(argv, parser = None):
    parser = OptionParser()
    parser.add_option("--run",                default = False, action="store_true")
    parser.add_option("--verbose",            default = False, action="store_true")
    parser.add_option("--expand-nodes",       default = False, action="store_true")
    parser.add_option("--max-threads",        default = 12, type = int)
    
    (options, args) = parser.parse_args(argv)

    makefiles = pypeline.tools.root_pipeline.makefile.read_makefiles(args)
    if not makefiles:
        return None, None
    
    return options, makefiles
