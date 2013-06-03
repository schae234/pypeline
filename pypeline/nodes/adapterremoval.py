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

from pypeline.node import CommandNode
from pypeline.atomiccmd import AtomicCmd, CmdError
from pypeline.atomicset import ParallelCmds
from pypeline.atomicparams import *

import pypeline.common.versions as versions


VERSION_14 = "1.4"
_VERSION_14_CHECK = versions.Requirement(call   = ("AdapterRemoval", "--version"),
                                         search = r"ver. (\d+)\.(\d+)",
                                         pprint = "{0}.{1}",
                                         checks = versions.EQ(1, 4))

VERSION_15 = "1.5+"
_VERSION_15_CHECK = versions.Requirement(call   = ("AdapterRemoval", "--version"),
                                         search = r"ver. (\d+)\.(\d+)",
                                         pprint = "{0}.{1}",
                                         checks = versions.EQ(1, 5))


class SE_AdapterRemovalNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(cls, input_files, output_prefix, output_format = "bz2", version = VERSION_15, dependencies = ()):
        # See below for parameters in common between SE/PE
        cmd = _get_common_parameters(version)

        # Uncompressed reads (piped from unicat)
        cmd.set_parameter("--file1",    "%(TEMP_IN_READS)s")

        # Prefix for output files
        cmd.set_parameter("--basename", "%(TEMP_OUT_BASENAME)s")

        basename = os.path.basename(output_prefix)
        cmd.set_paths(# Only settings file is saved, rest is temporary files
                      OUT_SETTINGS        = output_prefix + ".settings",
                      TEMP_OUT_BASENAME   = basename,

                      # Named pipe for uncompressed input (unicat)
                      TEMP_IN_READS       = "uncompressed_input",

                      # Named pipes for output of AdapterRemova
                      TEMP_OUT_LINK_1     = basename + ".truncated",
                      TEMP_OUT_LINK_2     = basename + ".discarded",
                      TEMP_OUT_LINK_3     = "uncompressed_input")

        return {"basename"      : basename,
                "format"        : output_format,
                "version"       : version,
                "command"       : cmd}


    @use_customizable_cli_parameters
    def __init__(self, parameters):
        self._basename = parameters.basename

        zcat           = _build_unicat_command(parameters.input_files, "uncompressed_input")
        zip_truncated  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".truncated")
        zip_discarded  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".discarded")
        adapterrm      = parameters.command.finalize()

        # Opening of pipes block, so the order of these commands is dependent upon
        # the order of file-opens in atomiccmd and the the programs themselves.
        commands = ParallelCmds([adapterrm, zip_discarded, zip_truncated, zcat])
        CommandNode.__init__(self,
                             command      = commands,
                             description  = "<SE_AdapterRM: %s -> '%s.*'>" \
                                 % (self._desc_files(parameters.input_files),
                                    parameters.output_prefix),
                             dependencies = parameters.dependencies)


    def _setup(self, config, temp):
        os.mkfifo(os.path.join(temp, self._basename + ".truncated"))
        os.mkfifo(os.path.join(temp, self._basename + ".discarded"))
        os.mkfifo(os.path.join(temp, "uncompressed_input"))

        CommandNode._setup(self, config, temp)




class PE_AdapterRemovalNode(CommandNode):
    @create_customizable_cli_parameters
    def customize(self, input_files_1, input_files_2, output_prefix, output_format = "bz2", version = VERSION_15, dependencies = ()):
        cmd = _get_common_parameters(version)
        # Merge pairs where the sequence is overlapping
        cmd.set_parameter("--collapse")

        # Uncompressed mate 1 and 2 reads (piped from unicat)
        cmd.set_parameter("--file1",    "%(TEMP_IN_READS_1)s")
        cmd.set_parameter("--file2",    "%(TEMP_IN_READS_2)s")

        # Prefix for output files, ensure that all end up in temp folder
        cmd.set_parameter("--basename", "%(TEMP_OUT_BASENAME)s")
        # Output files are explicity specified, to ensure that the order is the same here
        # as below. A difference in the order in which files are opened can cause a deadlock,
        # due to the use of named pipes (see __init__).
        cmd.set_parameter("--output1", "%(TEMP_OUT_LINK_PAIR1)s")
        cmd.set_parameter("--output2", "%(TEMP_OUT_LINK_PAIR2)s")
        cmd.set_parameter("--outputcollapsed", "%(TEMP_OUT_LINK_ALN)s")
        if version == VERSION_15:
            cmd.set_parameter("--outputcollapsedtruncated", "%(TEMP_OUT_LINK_ALN_TRUNC)s")
        cmd.set_parameter("--singleton", "%(TEMP_OUT_LINK_UNALN)s")
        cmd.set_parameter("--discarded", "%(TEMP_OUT_LINK_DISC)s")

        basename = os.path.basename(output_prefix)
        cmd.set_paths(# Only settings file is saved, rest is temporary files
                      OUT_SETTINGS        = output_prefix + ".settings",
                      TEMP_OUT_BASENAME   = basename,

                      # Named pipes for uncompressed input (unicat)
                      TEMP_IN_READS_1     = "uncompressed_input_1",
                      TEMP_IN_READS_2     = "uncompressed_input_2",

                      # Named pipes for output of AdapterRemoval
                      TEMP_OUT_LINK_PAIR1 = basename + ".pair1.truncated",
                      TEMP_OUT_LINK_PAIR2 = basename + ".pair2.truncated",
                      TEMP_OUT_LINK_DISC  = basename + ".discarded",
                      TEMP_OUT_LINK_6     = "uncompressed_input_1",
                      TEMP_OUT_LINK_7     = "uncompressed_input_2")

        if version == VERSION_15:
            cmd.set_paths(TEMP_OUT_LINK_ALN       = basename + ".collapsed",
                          TEMP_OUT_LINK_ALN_TRUNC = basename + ".collapsed.truncated",
                          TEMP_OUT_LINK_UNALN     = basename + ".singleton.truncated")
        elif version == VERSION_14:
            cmd.set_paths(TEMP_OUT_LINK_ALN       = basename + ".singleton.aln.truncated",
                          TEMP_OUT_LINK_UNALN     = basename + ".singleton.unaln.truncated")
        else:
            assert False

        return {"basename"       : basename,
                "format"         : output_format,
                "command"        : cmd}


    @use_customizable_cli_parameters
    def __init__(self, parameters):
        self._version    = parameters.version
        self._basename   = parameters.basename
        if len(parameters.input_files_1) != len(parameters.input_files_2):
            raise CmdError("Number of mate 1 files differ from mate 2 files: %i != %i" \
                               % (len(parameters.input_files_1),
                                  len(parameters.input_files_2)))

        zcat_pair_1    = _build_unicat_command(parameters.input_files_1, "uncompressed_input_1")
        zcat_pair_2    = _build_unicat_command(parameters.input_files_2, "uncompressed_input_2")
        zip_pair_1     = _build_zip_command(parameters.output_format, parameters.output_prefix, ".pair1.truncated")
        zip_pair_2     = _build_zip_command(parameters.output_format, parameters.output_prefix, ".pair2.truncated")
        zip_discarded  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".discarded")
        adapterrm      = parameters.command.finalize()

        commands = [adapterrm, zip_pair_1, zip_pair_2]
        if parameters.version == VERSION_15:
            zip_aln        = _build_zip_command(parameters.output_format, parameters.output_prefix, ".collapsed")
            zip_aln_trunc  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".collapsed.truncated")
            zip_unaligned  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".singleton.truncated")
            commands      += [zip_aln, zip_aln_trunc, zip_unaligned]
        else:
            zip_aln        = _build_zip_command(parameters.output_format, parameters.output_prefix, ".singleton.aln.truncated")
            zip_unaligned  = _build_zip_command(parameters.output_format, parameters.output_prefix, ".singleton.unaln.truncated")
            commands      += [zip_aln, zip_unaligned]
        commands += [zip_discarded, zcat_pair_1, zcat_pair_2]

        # Opening of pipes block, so the order of these commands is dependent upon
        # the order of file-opens in atomiccmd and the the programs themselves.
        commands = ParallelCmds(commands)

        description  = "<PE_AdapterRM: %s -> '%s.*'>" \
            % (self._desc_files(parameters.input_files_1).replace("file", "pair"),
               parameters.output_prefix)

        CommandNode.__init__(self,
                             command      = commands,
                             description  = description,
                             dependencies = parameters.dependencies)


    def _setup(self, config, temp):
        os.mkfifo(os.path.join(temp, self._basename + ".discarded"))
        os.mkfifo(os.path.join(temp, self._basename + ".pair1.truncated"))
        os.mkfifo(os.path.join(temp, self._basename + ".pair2.truncated"))
        os.mkfifo(os.path.join(temp, "uncompressed_input_1"))
        os.mkfifo(os.path.join(temp, "uncompressed_input_2"))

        if self._version == VERSION_15:
            os.mkfifo(os.path.join(temp, self._basename + ".collapsed"))
            os.mkfifo(os.path.join(temp, self._basename + ".collapsed.truncated"))
            os.mkfifo(os.path.join(temp, self._basename + ".singleton.truncated"))
        else:
            os.mkfifo(os.path.join(temp, self._basename + ".singleton.aln.truncated"))
            os.mkfifo(os.path.join(temp, self._basename + ".singleton.unaln.truncated"))

        CommandNode._setup(self, config, temp)



def _build_unicat_command(input_files, output_file):
    paths = {"TEMP_OUT_CAT" : output_file}
    call = ["unicat", "--output", "%(TEMP_OUT_CAT)s"]
    for (index, filename) in enumerate(safe_coerce_to_tuple(input_files)):
        key = "IN_CAT_%02i" % index

        call.append("%%(%s)s" % key)
        paths[key] = filename

    return AtomicCmd(call, **paths)


def _build_zip_command(output_format, prefix, name, output = None):
    if output_format == "bz2":
        command, ext = "bzip2", ".bz2"
    elif output_format == "gz":
        command, ext = "gzip", ".gz"
    else:
        raise CmdError("Invalid output-format (%s), please select 'gz' or 'bz2'" \
                       % repr(output_format))

    basename = os.path.basename(prefix)
    return AtomicCmd([command, "-c"],
                     TEMP_IN_STDIN = basename + name,
                     OUT_STDOUT    = prefix + (output or name) + ext)


def _get_common_parameters(version):
    if version == VERSION_14:
        version_check = _VERSION_14_CHECK
    elif version == VERSION_15:
        version_check = _VERSION_15_CHECK
    else:
        raise CmdError("Unknown version: %s" % version)

    cmd = AtomicParams("AdapterRemoval",
                       CHECK_VERSION = version_check)

    # Allow 1/3 mismatches in the aligned region
    cmd.set_parameter("--mm", 3, fixed = False)
    # Minimum length of trimmed reads
    cmd.set_parameter("--minlength", 25, fixed = False)
    # Trim Ns at read ends
    cmd.set_parameter("--trimns", fixed = False)
    # Trim low quality scores
    cmd.set_parameter("--trimqualities", fixed = False)
    # Offset of quality scores
    cmd.set_parameter("--qualitybase", 33, fixed = False)

    return cmd
