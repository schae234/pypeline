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
import types

from pypeline.common.makefile import \
     read_makefile, \
     validate_makefile, \
     MakefileError, \
     IsStr, \
     IsDictOf, \
     IsListOf, \
     AnyOf, \
     OneOf, \
     IsInt, \
     IsUnsignedInt, \
     IsBoolean, \
     IsStrWithPrefix, \
     CLI_PARAMETERS, \
     Or


class MAKEFileError(RuntimeError):
    pass

# TODO Implement default makefile
def default():
    return 1

def read_makefiles(filenames):
    makefiles = []
    for filename in filenames:
        makefile = read_makefile(filename, _DEFAULTS, _VALIDATION)
        makefile = makefile["Makefile"] # Not using extra stats
        makefiles.append(makefile)
    return makefiles

def IsValidPrefixName(key, value):
    return 1

def _IsValidPipeline(path,value):
    return 1 


_DEFAULTS = {
   "Options" : {
        },
    "References" : {
    },
    "Pipeline" : {
    }
}

_VALIDATION = {
    "Options" : {
    },
    "References" : {
        IsValidPrefixName : {
            "Path" : IsStr,
            "Label" : IsStr,
        },
    },
    "Pipeline" : {
    }
}
