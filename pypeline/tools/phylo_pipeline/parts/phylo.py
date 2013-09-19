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
#!/usr/bin/python

import os
import sys

from pypeline import Pypeline
from pypeline.node import MetaNode
from pypeline.nodes.formats import FastaToPartitionedInterleavedPhyNode
from pypeline.nodes.raxml import *
from pypeline.nodes.mafft import MetaMAFFTNode

from . import common


def build_supermatrix(options, settings, afa_ext, destination, intervals, taxa, filtering_postfix, dependencies):
    input_files = {}
    for interval in intervals.values():
        sequencedir = os.path.join(options.destination, "alignments", interval["Name"] + filtering_postfix)

        for sequence in common.collect_sequences(options, interval, taxa):
            filename = os.path.join(sequencedir, sequence + afa_ext)
            record = {"name" : sequence}
            if interval["Protein coding"]:
                record["partition_by"] = ("12", "12", "3")

            assert filename not in input_files, filename
            input_files[filename] = record


    excluded_groups = settings.get("ExcludeGroups", ())
    matrixprefix = os.path.join(destination, "alignments")
    supermatrix  = FastaToPartitionedInterleavedPhyNode(infiles        = input_files,
                                                        out_prefix     = matrixprefix,
                                                        partition_by   = "111",
                                                        exclude_groups = excluded_groups,
                                                        dependencies   = dependencies)

    return RAxMLReduceNode(input_alignment  = matrixprefix + ".phy",
                           output_alignment = matrixprefix + ".reduced.phy",
                           input_partition  = matrixprefix + ".partitions",
                           output_partition = matrixprefix + ".reduced.partitions",
                           dependencies     = supermatrix)


def _examl_nodes(settings, destination, input_alignment, input_binary, dependencies):
    initial_tree = os.path.join(destination, "initial.tree")

    tree = ParsimonatorNode(input_alignment = input_alignment,
                            output_tree     = initial_tree,
                            dependencies    = dependencies)

    return EXaMLNode(input_binary    = input_binary,
                     initial_tree    = initial_tree,
                     output_template = os.path.join(destination, "RAxML_%s"),
                     threads         = settings["ExaML"].get("Threads", 1),
                     dependencies    = tree)


def build_examl_nodes(options, settings, intervals, taxa, filtering, dependencies):
    filtering_postfix = ".filtered" if any(filtering.values()) else ""
    destination = os.path.join(options.destination, "phylogenies", "examl.supermatrix" + filtering_postfix)
    phylo = settings["Phylogenetic Inference"]
    afa_ext = ".afa" if settings["MSAlignment"]["Enabled"] else ".fasta"

    input_alignment = os.path.join(destination, "alignments.reduced.phy")
    input_partition = os.path.join(destination, "alignments.reduced.partitions")
    input_binary    = os.path.join(destination, "alignments.reduced.binary")

    supermatrix = build_supermatrix(options, phylo, afa_ext, destination, intervals, taxa, filtering_postfix, dependencies)
    binary      = EXaMLParserNode(input_alignment = input_alignment,
                                  input_partition = input_partition,
                                  output_file     = input_binary,
                                  dependencies    = supermatrix)

    replicates = []
    for replicate_num in range(phylo["ExaML"]["Replicates"]):
        replicate_destination = os.path.join(destination, "replicate_%04i" % replicate_num)
        replicates.append(_examl_nodes(phylo, replicate_destination, input_alignment, input_binary, binary))

    bootstraps = []
    for bootstrap_num in range(phylo["ExaML"]["Bootstraps"]):
        bootstrap_destination = os.path.join(destination, "bootstrap_%04i" % bootstrap_num)
        bootstrap_alignment   = os.path.join(bootstrap_destination, "bootstrap.phy")
        bootstrap_binary      = os.path.join(bootstrap_destination, "bootstrap.binary")

        bootstrap   = RAxMLBootstrapNode(input_alignment  = input_alignment,
                                         input_partition  = input_partition,
                                         output_alignment = bootstrap_alignment,
                                         dependencies     = supermatrix)

        bs_binary   = EXaMLParserNode(input_alignment = bootstrap_alignment,
                                      input_partition = input_partition,
                                      output_file     = bootstrap_binary,
                                      dependencies    = bootstrap)

        bootstraps.append(_examl_nodes(phylo, bootstrap_destination, bootstrap_alignment, bootstrap_binary, bs_binary))

    dependencies = []
    if replicates:
        dependencies.append(MetaNode(description  = "Replicates",
                                     subnodes     = replicates,
                                     dependencies = binary))
    if bootstraps:
        dependencies.append(MetaNode(description  = "Bootstraps",
                                     subnodes     = bootstraps,
                                     dependencies = supermatrix))

    return MetaNode(description = "EXaML",
                    dependencies = dependencies)


def chain_examl(pipeline, options, makefiles):
    destination = options.destination # Move to makefile
    for makefile in makefiles:
        taxa      = makefile["Project"]["Taxa"]
        intervals = makefile["Project"]["Intervals"]
        filtering = makefile["Project"]["Filter Singletons"]
        options.destination = os.path.join(destination, makefile["Project"]["Title"])

        makefile["Nodes"] = build_examl_nodes(options, makefile, intervals, taxa, filtering, makefile["Nodes"])
    options.destination = destination
