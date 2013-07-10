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
import copy
import re

from pypeline.common.fileutils import missing_files
from pypeline.common.makefile import MakefileError
from pypeline.nodes.adapterremoval import SE_AdapterRemovalNode, \
                                          PE_AdapterRemovalNode, \
                                          VERSION_14, \
                                          VERSION_15

import pypeline.tools.bam_pipeline.paths as paths


class Reads:
    def __init__(self, config, record, quality_offset):
        self.quality_offset = quality_offset
        self.files = {}
        self.stats = None
        self.nodes = ()

        tags = record["Tags"]
        self.folder = os.path.join(config.destination, tags["Target"], "reads",
                                   tags["SM"], tags["LB"], tags["PU_cur"])

        lane_type = record.get("Type")
        if lane_type == "Raw":
            self._init_raw_reads(config, record)
        elif lane_type == "Trimmed":
            self.files.update(record["Data"])
        else:
            assert False, "Unexpected data type in Reads(): %s" % (repr(lane_type))

        # Check Quality Score
        if not self._check_raw_read_quality(record):
            assert False, "Quality Scores do not match: %s" % (repr(record["Data"]))

        for name in record["Options"]["ExcludeReads"]:
            self.files.pop(name, None)

        if config.allow_missing_input_files and self.nodes:
            input_missing  = missing_files(self.nodes[0].input_files)
            output_missing = missing_files(self.nodes[0].output_files)
            if input_missing and not output_missing:
                self.nodes = ()


    def _init_raw_reads(self, config, record):
        version = VERSION_14
        if record["Options"]["AdapterRemoval"]["Version"] == "v1.5+":
            version = VERSION_15

        output_format = record["Options"]["CompressionFormat"]
        output_prefix = os.path.join(self.folder, "reads")
        files = record["Data"]
        if ("SE" in files):
            command = SE_AdapterRemovalNode.customize(input_files   = files["SE"],
                                                      output_prefix = output_prefix,
                                                      output_format = output_format,
                                                      version       = version)
            self.files["Single"] = output_prefix + ".truncated." + output_format
        else:
            command = PE_AdapterRemovalNode.customize(input_files_1 = files["PE_1"],
                                                      input_files_2 = files["PE_2"],
                                                      output_prefix = output_prefix,
                                                      output_format = output_format,
                                                      version       = version)
            self.files["Paired"]    = output_prefix + ".pair{Pair}.truncated." + output_format
            if version is VERSION_14:
                self.files["Single"]    = output_prefix + ".singleton.unaln.truncated."  + output_format
                self.files["Collapsed"] = output_prefix + ".singleton.aln.truncated." + output_format
            else:
                self.files["Single"]    = output_prefix + ".singleton.truncated."  + output_format
                self.files["Collapsed"] = output_prefix + ".collapsed." + output_format
                self.files["CollapsedTruncated"] = output_prefix + ".collapsed.truncated." + output_format

        self.stats = output_prefix + ".settings"

        quality_offset = self.quality_offset # record["Options"]["QualityOffset"]
        if quality_offset == "Solexa":
            quality_offset = 64
        command.command.set_parameter("--qualitybase", quality_offset)

        self.nodes = (command.build_node(),)


    def _check_raw_read_quality(self, record):
        # dont check the whole file
        lines = 10000
        def detect_phred_offset(fastq_file_name):
            # set initial version detections to 0
            v33 = 0
            v64 = 0
            # input files can be compressed in gzip of bzip
            if re.match("^.*gz|gzip$",fastq_file_name):
                import gzip
                fastq_file = gzip.open(fastq_file_name, 'rb')
            elif re.match("^.*.bz2|bzip$"):
                import bz2
                fastq_file = bz2.BZ2File(fastq_file_name)
            else:
                fastq_file = open(fastq_file_name,'r')
            # dont read the whole file
            for n in range(1,lines):
                line = fastq_file.readline().rstrip("\n")
                if n % 4 != 0:
                    continue
                # v33 have these unique ascii encodings
                if re.search(r'[!i"#$%&\'()*+,-./0123456789:;<=>?]',line):
                    v33 += 1
                # v64 have these unique ascii encodings
                if re.search(r"[KLMNOPQRSTUVWXYZ[]^_`abcdefgh]",line):
                    v64 += 1 
            if v33 > v64:
                return 33
            elif v33 < v64:
                return 64
        # Test the files
        files = record["Data"]
        for file_names in files.itervalues():
            for file_name in file_names:
                if detect_phred_offset(file_name) != self.quality_offset:
                    return False
        # all the files detected were what expected
        return True 
