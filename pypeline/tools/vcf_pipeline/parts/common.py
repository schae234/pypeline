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
import ConfigParser

from optparse import OptionParser
import pypeline.tools.vcf_pipeline.makefile
import pypeline.ui as ui


def parse_options(argv, parser = None):
    # Read Deaults
    defaults = _parse_defaults()

    parser = OptionParser()
    parser.add_option("--run",                default = True, action="store_true")
    parser.add_option("--verbose",            default = False, action="store_true")
    parser.add_option("--expand-nodes",       default = False, action="store_true")
    parser.add_option("--max-threads",        default = 12, type = int)
    parser.add_option("--temp-root",          default = "./Variant_Temp")
    parser.add_option("--destination",        default = "./Variant_Results")
    parser.add_option("--jar-root",           default = os.path.expanduser(defaults.get("jar_root")))
    
    (options, args) = parser.parse_args(argv)

    makefiles = pypeline.tools.vcf_pipeline.makefile.read_makefiles(args)
    if not makefiles:
        return None, None
    
    return options, makefiles

def _parse_defaults():
    config = ConfigParser.SafeConfigParser()
    # Read In pypeline Defaults
    config_paths = (os.path.join(os.path.expanduser('~'), ".pypeline.conf"),
        "/etc/pypeline.conf")
    for config_path in config_paths:
        if os.path.exists(config_path):
            config.read(config_path)
            break
    try:
        defaults = dict(config.items("Defaults"))
    except ConfigParser.NoSectionError:
        defaults = {}
    return defaults
