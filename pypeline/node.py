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
import sys
import types
import pickle
import traceback
import collections

import pypeline.common.fileutils as fileutils
from pypeline.common.utilities import safe_coerce_to_frozenset, \
     fast_pickle_test




class NodeError(RuntimeError):
    pass

class CmdNodeError(NodeError):
    pass

class MetaNodeError(NodeError):
    pass

class NodeUnhandledException(NodeError):
    """This exception is thrown by Node.run() if a non-NodeError exception
    is raised in a subfunction (e.g. _setup, _run, or _teardown). The text
    for this exception will include both the original error message and a
    stacktrace for that error."""
    pass


class Node(object):
    def __init__(self, description = None, threads = 1,
                 input_files = (), output_files = (),
                 executables = (), auxiliary_files = (),
                 requirements = (), subnodes = (), dependencies = ()):

        if not isinstance(description, _DESC_TYPES):
            raise TypeError("'description' must be None or a string, not %r" \
                            % (description.__class__.__name__,))

        self.__description   = description
        self.input_files     = self._validate_files(input_files)
        self.output_files    = self._validate_files(output_files)
        self.executables     = self._validate_files(executables)
        self.auxiliary_files = self._validate_files(auxiliary_files)
        self.requirements    = self._validate_requirements(requirements)

        self.subnodes        = frozenset()
        self.dependencies    = frozenset()
        self.threads         = self._validate_nthreads(threads)

        try:
            # Ensure that the node can be used in a multiprocessing context
            fast_pickle_test(self)
        except pickle.PicklingError, error:
            raise NodeError("Node could not be pickled, please file a bug-report:\n"
                            "\tNode: %s\n\tError: %s" % (self, error))

        # Set here to avoid pickle-testing of subnodes / dependencies
        self.subnodes        = self._collect_nodes(subnodes, "Subnode")
        self.dependencies    = self._collect_nodes(dependencies, "Dependency")


    @property
    def is_done(self):
        """Returns true if all subnodes of this node are done, and if all output
        files of this node exists (empty files are considered as valid). If the
        node doesn't produce output files, it is always considered done by. To
        change this behavior, override the 'is_done' property"""

        if not all(node.is_done for node in self.subnodes):
            return False
        elif fileutils.missing_files(self.output_files):
            return False

        return True


    @property
    def is_outdated(self):
        """Returns true if the output exists (is_done == True), but one or more
        of the intput files appear to have been changed since the creation of the
        output files (based on the timestamps). A node that lacks either input or
        output files is never considered outdated."""

        if not self.is_done:
            return False
        elif not (self.input_files and self.output_files):
            return False

        return fileutils.modified_after(self.input_files, self.output_files)


    def run(self, config):
        """Runs the node, by calling _setup, _run, and _teardown in that order.
        Prior to calling these functions, a temporary dir is created using the
        'temp_root' prefix from the config object. Both the config object and
        the temporary dir are passed to the above functions. The temporary
        dir is removed after _teardown is called, and all expected files
        should have been removed/renamed at that point.

        Any non-NodeError exception raised in this function is wrapped in a
        NodeUnhandledException, which includes a full backtrace. This is needed
        to allow showing these in the main process."""

        try:
            temp = None
            temp = fileutils.create_temp_dir(config.temp_root)

            self._setup(config, temp)
            self._run(config, temp)
            self._teardown(config, temp)

            os.rmdir(temp)
        except NodeError, error:
            self._write_error_log(temp, error)
            raise error
        except Exception, error:
            self._write_error_log(temp, error)
            error = NodeUnhandledException(traceback.format_exc())
            raise error


    def _setup(self, _config, _temp):
        """Is called prior to '_run()' by 'run()'. Any code used to copy/link files,
        or other steps needed to ready the node for running may be carried out in this
        function. Checks that required input files exist, and raises an NodeError if
        this is not the case."""
        if fileutils.missing_executables(self.executables):
            raise NodeError("Executable(s) does not exist for node: %s" % (self,))
        self._check_for_missing_files(self.input_files, "input")
        self._check_for_missing_files(self.auxiliary_files, "auxiliary")


    def _run(self, _config, _temp):
        pass

    def _teardown(self, _config, _temp):
        self._check_for_missing_files(self.output_files, "output")

    def __str__(self):
        """Returns the description passed to the constructor, or a default
        description if no description was passed to the constructor."""
        if self.__description:
            return self.__description
        return repr(self)


    def _write_error_log(self, temp, error):
        if temp and os.path.isdir(temp):
            with open(os.path.join(temp, "pipe.errors"), "w") as handle:
                handle.write("Command          = %s\n" % " ".join(sys.argv))
                handle.write("CWD              = %s\n\n" % os.getcwd())
                handle.write("Node             = %s\n" % str(self))
                handle.write("Threads          = %i\n" % self.threads)

                prefix =   "\n                   "
                handle.write("Input files      = %s\n" % (prefix.join(sorted(self.input_files))))
                handle.write("Output files     = %s\n" % (prefix.join(sorted(self.output_files))))
                handle.write("Auxiliary files  = %s\n" % (prefix.join(sorted(self.auxiliary_files))))
                handle.write("Executables      = %s\n" % (prefix.join(sorted(self.executables))))

                handle.write("\nErrors =\n%s\n" % error)


    def _collect_nodes(self, nodes, description):
        if nodes is None:
            return frozenset()

        nodes = safe_coerce_to_frozenset(nodes)
        bad_nodes = [node for node in nodes if not isinstance(node, Node)]

        if bad_nodes:
            bad_nodes = [repr(node) for node in bad_nodes]
            message = "%s-list contain non-Node objects:\n\t- Command: %s\n\t- Objects: %s" \
                % (description, self, "\n\t           ".join(bad_nodes))
            raise TypeError(message)

        return nodes


    def _check_for_missing_files(self, filenames, description):
        missing_files = fileutils.missing_files(filenames)
        if missing_files:
            message = "Missing %s files for command:\n\t- Command: %s\n\t- Files: %s" \
                % (description, self, "\n\t         ".join(missing_files))
            raise NodeError(message)

    @classmethod
    def _validate_requirements(cls, requirements):
        requirements = safe_coerce_to_frozenset(requirements)
        for requirement in requirements:
            if not isinstance(requirement, collections.Callable):
                raise TypeError("'requirements' must be callable, not %r" \
                    % (type(requirement),))
        return requirements

    @classmethod
    def _validate_files(cls, files):
        files = safe_coerce_to_frozenset(files)
        for filename in files:
            if not isinstance(filename, types.StringTypes):
                raise TypeError('Files must be strings, not %r' % filename.__class__.__name__)
        return files

    @classmethod
    def _validate_nthreads(cls, threads):
        if not isinstance(threads, (types.IntType, types.LongType)):
            raise TypeError("'threads' must be a positive integer, not %s" % (type(threads),))
        elif threads < 1:
            raise ValueError("'threads' must be a positive integer, not %i" % (threads,))
        return int(threads)




class CommandNode(Node):
    def __init__(self, command, description = None, threads = 1,
                 subnodes = (), dependencies = ()):
        Node.__init__(self,
                      description  = description,
                      input_files  = command.input_files,
                      output_files = command.output_files,
                      auxiliary_files = command.auxiliary_files,
                      executables  = command.executables,
                      requirements = command.requirements,
                      threads      = threads,
                      subnodes     = subnodes,
                      dependencies = dependencies)

        self._command = command

    def _run(self, _config, temp):
        """Runs the command object provided in the constructor, and waits for it to
        terminate. If any errors during the running of the command, this function
        raises a NodeError detailing the returned error-codes."""
        self._command.run(temp)

        return_codes = self._command.join()
        if any(return_codes):
            desc = "\n\t".join(str(self._command).split("\n"))
            raise CmdNodeError(("Error(s) running Node:\n\tReturn-codes: %s\n"
                                "\tTemporary directory: %s\n\n\t%s") \
                                % (return_codes, repr(temp), desc))


    def _teardown(self, config, temp):
        required_files = self._command.expected_temp_files
        optional_files = self._command.optional_temp_files
        current_files  = set(os.listdir(temp))

        missing_files = (required_files - current_files)
        if missing_files:
            raise CmdNodeError(("Error running Node, required files not created:\n"
                               "Temporary directory: %r\n"
                               "\tRequired files missing from temporary directory:\n\t    - %s") \
                               % (temp, "\n\t    - ".join(sorted(map(repr, missing_files)))))

        extra_files = current_files - (required_files | optional_files)
        if extra_files:
            raise CmdNodeError("Error running Node, unexpected files created:\n"
                               "\tTemporary directory: %r\n"
                               "\tUnexpected files found in temporary directory:\n\t    - %s" \
                               % (temp, "\n\t    - ".join(sorted(map(repr, extra_files)))))

        self._command.commit(temp)

        Node._teardown(self, config, temp)



class MetaNode(Node):
    """A MetaNode is a simplified node, which only serves the purpose of aggregating
    a set of subnodes. It does not carry out any task itself (run() does nothing),
    and is marked as done when all its subnodes / dependencies are completed."""

    def __init__(self, description = None, subnodes = (), dependencies = ()):
        Node.__init__(self,
                      description  = description,
                      subnodes     = subnodes,
                      dependencies = dependencies)

    @property
    def is_done(self):
        raise MetaNodeError("Called 'is_done' on MetaNode")

    @property
    def is_outdated(self):
        raise MetaNodeError("Called 'is_outdated' on MetaNode")

    def run(self, config):
        raise MetaNodeError("Called 'run' on MetaNode")



# Types that are allowed for the 'description' property
_DESC_TYPES = types.StringTypes + (types.NoneType,)
