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
import datetime
import collections

import pysam

from pypeline.node import Node
from pypeline.common.text import padded_table, parse_padded_table
from pypeline.common.fileutils import reroot_path, move_file, swap_ext, describe_files
from pypeline.common.utilities import get_in, set_in


_MAX_CONTIGS = 100


class CoverageNode(Node):
    def __init__(self, input_file, target_name, output_file = None, intervals_file = None, max_contigs = _MAX_CONTIGS, dependencies = ()):
        self._target_name = target_name
        self._input_file  = input_file
        self._output_file = output_file or swap_ext(input_file, ".coverage")
        self._intervals_file = intervals_file
        self._max_contigs = max_contigs
        self._max_contigs_reached = False

        Node.__init__(self,
                      description  = "<Coverage: '%s' -> '%s'>" \
                          % (input_file, self._output_file),
                      input_files  = (input_file, swap_ext(input_file, ".bai")),
                      output_files = self._output_file,
                      dependencies = dependencies)


    def _setup(self, _config, temp):
        bam_filename  = os.path.abspath(self._input_file)
        temp_filename = reroot_path(temp, bam_filename)

        os.symlink(bam_filename, temp_filename)
        os.symlink(swap_ext(bam_filename, ".bai"), temp_filename + ".bai")


    def _run(self, _config, temp):
        temp_filename = reroot_path(temp, self._input_file)

        with pysam.Samfile(temp_filename) as bamfile:
            intervals = self._get_intervals(bamfile, self._intervals_file, self._max_contigs)
            readgroups = self._get_readgroups(bamfile)

            tables, mapping = self._initialize_tables(self._target_name, intervals, readgroups)
            self.read_records(bamfile, intervals, mapping)

        tables = self.filter_readgroups(tables)
        _write_table(tables, reroot_path(temp, self._output_file))


    def _teardown(self, config, temp):
        temp_filename = reroot_path(temp, self._input_file)
        os.remove(temp_filename)
        os.remove(temp_filename + ".bai")

        move_file(reroot_path(temp, self._output_file), self._output_file)
        Node._teardown(self, config, temp)


    @classmethod
    def _get_intervals(cls, bamfile, intervals_file, max_contigs):
        intervals = {}
        if not intervals_file:
            if len(bamfile.references) > max_contigs:
                return {"<Genome>" : [(None, 0, sum(bamfile.lengths))] }

            for (name, length) in zip(bamfile.references, bamfile.lengths):
                intervals[name] = [(name, 0, length)]

            return intervals

        with open(intervals_file) as handle:
            parser = pysam.asBed()
            for line in handle:
                bed = parser(line, len(line))
                name = bed.name if len(bed) >= 4 else (bed.contig + "*")
                if name not in intervals:
                    intervals[name] = []
                intervals[name].append((bed.contig, bed.start, bed.end))
        return intervals


    @classmethod
    def _get_readgroups(cls, bamfile):
        readgroups = {None : {"ID" : None, "SM" : "<NA>", "LB" : "<NA>"}}
        for readgroup in bamfile.header.get('RG', []):
            readgroups[readgroup["ID"]] = readgroup

        return readgroups


    @classmethod
    def _initialize_tables(cls, target_name, intervals, readgroups):
        subtables = {}
        for (name, intervals) in intervals.iteritems():
            size = sum((end - start) for (_, start, end) in intervals)
            subtables[name] = {"SE" : 0, "PE_1" : 0, "PE_2" : 0, "Collapsed" : 0, "Hits" : 0, "M" : 0, "I" : 0, "D" : 0, "Size" : size}

        tables, mapping = {}, {}
        for rg in readgroups.itervalues():
            subtbl_copy = get_in(tables, (target_name, rg["SM"], rg["LB"]), None)
            if not subtbl_copy:
                subtbl_copy = copy.deepcopy(subtables)

            set_in(tables, (target_name, rg["SM"], rg["LB"]), subtbl_copy)
            mapping[rg["ID"]] = subtbl_copy

        return tables, mapping


    @classmethod
    def read_records(cls, bamfile, intervals, tables):
        def _get_readgroup(record):
            for key, value in record.tags:
                if key == "RG":
                    return value

        for (name, interval_list) in intervals.iteritems():
            for (contig, start, end) in interval_list:
                keys = (contig, start, end)
                if contig is None:
                    keys = ()

                for record in bamfile.fetch(*keys):
                    if record.is_unmapped or record.is_duplicate:
                        continue

                    readgroup = _get_readgroup(record)
                    subtable  = tables[readgroup][name]

                    qname = record.qname
                    if qname.startswith("M_") or qname.startswith("MT_"):
                        subtable["Collapsed"] += 1
                    else:
                        flag = record.flag
                        if flag & 0x40: # first of pair
                            subtable["PE_1"] += 1
                        elif flag & 0x80: # second of pair
                            subtable["PE_2"] += 1
                        else: # Singleton
                            subtable["SE"] += 1

                    position = record.pos
                    for (op, num) in record.cigar:
                        if op < 3:
                            left  = min(max(position, start), end - 1)
                            right = min(max(position + num, start), end - 1)
                            subtable["MID"[op]] += right - left

                            if op < 2: # M/D
                                position += num
                        elif op == 3: # N
                            position += num


    def filter_readgroups(self, table):
        for (name, subtable) in table.iteritems():
            for (library, contigs) in subtable.get("<NA>", {}).iteritems():
                for (contig, counts) in contigs.iteritems():
                    if any(value for (key, value) in counts.iteritems() if key != "Size"):
                        return table

        for (name, subtable) in table.iteritems():
            subtable.pop("<NA>")

        return table



class MergeCoverageNode(Node):
    def __init__(self, input_files, output_file, dependencies = ()):
        self._output_file = output_file

        Node.__init__(self,
                      description  = "<MergeCoverage: '%s' -> '%s'>" \
                          % (describe_files(input_files), self._output_file),
                      input_files  = input_files,
                      output_files = self._output_file,
                      dependencies = dependencies)


    def _run(self, _config, temp):
        table = {}
        for filename in self.input_files:
            read_table(table, filename)

        _write_table(table, reroot_path(temp, self._output_file))
        move_file(reroot_path(temp, self._output_file), self._output_file)



def _calculate_totals(table):
    for (name, samples) in sorted(table.items()):
        for (sample, libraries) in sorted(samples.items()):
            for (library, contigs) in sorted(libraries.items()):
                set_in(table, (name, sample, library), _calculate_totals_in(contigs))
            set_in(table, (name, sample, "*"), _calculate_totals_in(libraries))
            set_in(table, (name, sample, "*", "*", "Size"), get_in(table, (name, sample, library, "*", "Size")))
        set_in(table, (name, "*", "*"), _calculate_totals_in(table))
        set_in(table, (name, "*", "*", "*", "Size"), get_in(table, (name, sample, "*", "*", "Size")))


def _calculate_totals_in(tables):
    def _defaults():
        return {"SE" : 0, "PE_1" : 0, "PE_2" : 0, "Collapsed" : 0, "Size" : 0, "Hits" : 0, "M" : 0, "I" : 0, "D" : 0}
    totals = collections.defaultdict(_defaults)

    subtables = tables.items()
    while subtables:
        subtable_key, subtable = subtables.pop()
        if subtable_key == "*":
            continue
        elif "SE" in subtable:
            for key in subtable:
                if key == "Size":
                    totals[subtable_key][key] = 0
                totals[subtable_key][key] += subtable[key]
                totals["*"][key] += subtable[key]
        else:
            subtables.extend(subtable.items())
    return totals


def _build_rows(table):
    rows = [("Name", "Sample", "Library", "Contig", "Size", "Hits", "SE", "PE_1", "PE_2", "Collapsed", "M", "I", "D", "Coverage")]
    for (name, samples) in sorted(table.items()):
        for (sample, libraries) in sorted(samples.items()):
            for (library, contigs) in sorted(libraries.items()):
                for (contig, subtable) in sorted(contigs.items()):
                    row = [name,
                           sample,
                           library,
                           contig,
                           subtable["Size"],
                           subtable["SE"] + subtable["PE_1"] + subtable["PE_2"] + subtable["Collapsed"],
                           subtable["SE"],
                           subtable["PE_1"],
                           subtable["PE_2"],
                           subtable["Collapsed"],
                           subtable["M"],
                           subtable["I"],
                           subtable["D"],
                           float(subtable["M"]) / subtable["Size"]]
                    rows.append(row)
                rows.append("#")
            rows.append("#")

    while rows[-1] == "#":
        rows.pop()
    return rows


def read_table(table, filename):
    with open(filename) as table_file:
        for record in parse_padded_table(table_file):
            key = (record["Name"], record["Sample"], record["Library"], record["Contig"])
            if "*" in key:
                continue

            subtable = get_in(table, key, {"Size" : int(record["Size"])})
            assert int(subtable["Size"]) == int(record["Size"])

            for field in ("Hits", "SE", "PE_1", "PE_2", "Collapsed", "M", "I", "D"):
                subtable[field] = subtable.get(field, 0) + int(record.get(field, 0))
            set_in(table, key, subtable)


def _write_table(table, filename):
    _calculate_totals(table)
    rows = _build_rows(table)
    with open(filename, "w") as table_file:
        table_file.write(_HEADER % datetime.datetime.now().isoformat())
        for line in padded_table(rows):
            table_file.write(line)
            table_file.write("\n")


_HEADER = \
"""# Timestamp: %s
#
# Columns:
#   Contig:       Contig, chromosome, or feature for which a depth histogram was
#                 created. Unnamed features are named after the chromosome or
#             contig on which they are located, with a star appended. For
#             example "chr1*".
#   Size:     The total size of the region. Multiple features with the same
#             name are combined into one row, with the size representing to
#                  total of these. Note that overlapping bases are counted 2 (or
#                  more) times.
#  Hits:           Sum of SE, PE_1, and PE_2 hits
#  SE, PE_1, PE_2: Number of Single Ended, and Pair Ended (mate 1 and 2) hits overlapping
#                  the current contig or intervals. Note that a hit may be counted multiple
#                  times if it overlaps multiple intervals
#  Collapsed:      Number of hits for PE pair collapsed into a single read
#  M, I, D:        Number of aligned (M), inserted (I) and deleted (D) bases relative to references
#  Coverage:       Average number of bases covering each position in the contig(s)/intervals(s).
"""
