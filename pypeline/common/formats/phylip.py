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
import itertools

from pypeline.common.utilities import grouper
from pypeline.common.formats.msa import validate_msa, MSAError


_NUM_BLOCKS      = 6
_BLOCK_SIZE      = 10
_BLOCK_SPACING   = 2
_MAX_NAME_LENGTH = 30
_NAME_ENDS_AT    = 36
_LINE_SIZE       = _NUM_BLOCKS * _BLOCK_SIZE + (_NUM_BLOCKS - 1) * _BLOCK_SPACING


def sequential_phy(msa, add_flag = False, max_name_length = _MAX_NAME_LENGTH):
    validate_msa(msa)
    header = "%i %i" % (len(msa), len(list(msa.values())[0]))
    if add_flag:
        header += " S"

    spacing = " " * _BLOCK_SPACING
    result = [header, ""]
    for (name, sequence) in sorted(msa.items()):
        result.append(name[:max_name_length])
        
        blocks = grouper(_BLOCK_SIZE, sequence, fillvalue = "")
        lines  = grouper(_NUM_BLOCKS, blocks)
        for line in lines:
            result.append(spacing.join("".join(block) for block in line if block))
        
    return "\n".join(result)
    


def interleaved_phy(msa, add_flag = False, max_name_length = _MAX_NAME_LENGTH):
    validate_msa(msa)
    header = "%i %i" % (len(msa), len(list(msa.values())[0]))
    if add_flag:
        header += " I"
    result = [header, ""]

    padded_len  = min(max_name_length, max(len(name) for name in msa)) + 2
    padded_len -= padded_len % -(_BLOCK_SIZE + _BLOCK_SPACING) + _BLOCK_SPACING

    streams = []
    spacing = " " * _BLOCK_SPACING
    for (name, sequence) in sorted(msa.items()):
        name    = name[:max_name_length]
        padding = (padded_len - len(name)) * " "
        
        lines = []
        line  = [name, padding]
        for block in grouper(_BLOCK_SIZE, sequence, fillvalue = ""):
            block = "".join(block)
            if sum(len(segment) for segment in line) >= _LINE_SIZE:
                lines.append("".join(line))
                line = [block]
            else:
                line.extend((spacing, block))

        lines.append("".join(line))
        streams.append(lines)

    for rows in zip(*streams):
        result.extend(row for row in rows)
        result.append("")
    result.pop()

    return "\n".join(result)
