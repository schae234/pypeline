#!/usr/bin/python

import sys

class Variant(object):
    def __init__(self,*arg,**kwargs):
        pass

class VCFBuffer(object):
    ''' 
        VCF class which allows you to compare variant entries to
        other entries within a buffer
        '''
    def __init__(self,filename):
        # Set up class variable
        self.max_buffer_size = 100
        # Set up class data structures
        self.header_buffer = []
        self.upstream = []
        self.current = []
        self.downstream = []
        # Set up some class files
        self.log = sys.stderr 
        self.file = open(filename,'r')
        # Set up the initial buffer
        self.down_buffer()


    def down_buffer(self):
        # Read in a line
        line = self.file.readline().strip()
        if line.startswith("#"):
            self.header_buffer.append(line)
        else:
            if line  == '':
                fields = []
            else:
                fields = line.split()
            self.downstream.append(fields)
        # Keep going until we have a full buffer
        if len(self.downstream) < self.max_buffer_size:
            self.down_buffer()


    def up_buffer(self):
        while len(self.current) > 1:
            self.upstream.append(self.current.pop(0))
        while len(self.upstream) > self.max_buffer_size:
            self.upstream.pop(0)
 
    def readline(self):
        # Take care of the downstream buffer
        self.down_buffer()
        # Take care of the current buffer
        self.current.append(self.downstream.pop(0))
        # Take care of the upstream buffer
        self.up_buffer()
        return self.current[0]

    def header(self):
        return "\n".join(self.header_buffer)

    def __iter__(self):
        return self


    def next(self):
        if self.readline() == []:
            raise StopIteration
        return self.current[0]


    def __str__(self):
        return '''
        Upstream:
            {}
        Current:
            {}
        Downstream:
            {}
        '''.format(
            "\n\t\t".join([",".join(i) for i in self.upstream]),
            "\n\t\t".join([",".join(i) for i in self.current]),
            "\n\t\t".join([",".join(i) for i in self.downstream]),
        )
 
