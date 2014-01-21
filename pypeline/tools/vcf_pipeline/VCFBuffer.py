#!/usr/bin/python

import sys

class VCF(object):
    def __init__(self,filename):
        pass

class Genotype(object):
    def __init__(self):
        pass

class Variant(VCF):
    def __init__(self,fields):
        self.fields = fields
    @property
    def chrom(self):
        return self.fields[0]
    @property
    def pos(self):
        return int(self.fields[1])
    @property
    def id(self):
        return self.fields[2]
    @property
    def ref(self):
        return self.fields[3]
    @property
    def alt(self):
        return self.fields[4]
    @property
    def qual(self):
        return float(self.fields[5])
    @property
    def filters(self):
        return(self.fields[6].split(';'))
    def info(self,ID):
        pass
    def format(self,ID):
        pass
    def genotypes(self):
        pass

    def __str__(self):
        return '[{},{},{}...]'.format(self.chrom,self.pos,self.id)


class VCFBuffer(object):
    ''' 
        VCF class which allows you to compare variant entries to
        other entries within a buffer.

        [ [], L1  ]


        '''
    def __init__(self,filename,buffer_function = 'max_size'):
        # Set up the buffer clearing function
        self.is_buffer_full = getattr(self,buffer_function)
        # Set up class variable
        self.max_buffer_size = 0
        self.window_size = 10 # in bp
        # Set up class data structures
        self.header_buffer = []
        self.buffer = []
        self.current = 0
        # Set up some class files
        self.log = sys.stderr 
        self.file = open(filename,'r')
        # Set up the initial buffer
        self.staged = self.nextvar()
        self.rebuffer()

    def nextvar(self):
        ''' return the next variant of the file, handles headers gracefully ''' 
        line = self.file.readline().strip() 
        while line.startswith('#'):
            self.header_buffer.append(line)
            line = self.file.readline().strip() 
        if line == '':
            return []
        else:
            return Variant(line.split())
 
    # Buffer Full functions
    def max_size(self,stream):
        ''' The buffer contains a maximum number of SNPs '''
        if stream == 'downstream':
            if len(self.buffer) - self.current <= self.max_buffer_size:
                return False
            else:
                return True
        elif stream == 'upstream':
            if self.current > self.max_buffer_size:
                return False
            else:
                return True
            
    def max_window(self,stream):
        ''' The buffer contains a maximum number of SNPs within a window ''' 
        if stream == 'downstream':
            if self.staged != [] and abs(self.staged.pos - self.buffer[self.current].pos) <= self.window_size:
                return False
            else:
                return True
        if stream == 'upstream':
            if abs(self.buffer[0].pos - self.buffer[self.current].pos) > self.window_size:
                return False
            else:
                return True

    def rebuffer(self):
        ''' adjusts buffer so that it satisfies the buffer function ''' 
        if len(self.buffer) == 0: # Beginning condition
            return
        while not self.is_buffer_full('downstream'):
            self.buffer.append(self.staged)
            self.staged = self.nextvar()
        while not self.is_buffer_full('upstream'):
            self.buffer.pop(0)
            self.current -= 1

    def readline(self):
        ''' returns the next variant in the buffer, handles rebuffering '''
        # Beginning condition
        if len(self.buffer) == 0:
            self.buffer.append(self.staged)
            self.staged = self.nextvar()
        elif self.current == len(self.buffer)-1:
            # End condition
            if self.staged == []:
                return self.staged
            self.buffer.append(self.staged)
            self.staged = self.nextvar()
            self.current += 1 # go to next in buffer
        else:        
            self.current += 1 # go to next in buffer
        self.rebuffer()
        return self.buffer[self.current] 

    def header(self):
        return "\n".join(self.header_buffer)

    def __iter__(self):
        return self

    def next(self):
        if self.readline() == []:
            raise StopIteration
        return self.buffer[self.current]


    def __str__(self):
        s = '''Buffer:\n-------\n'''
        for x,y in enumerate(self.buffer):
            if x == self.current:
                s+=str(y)+"<-- Current\n"
            else:
                s+=str(y)+"\n"
        s+='''Staged:\n-------\n{}'''.format(str(self.staged))
        return s
    def __repr__(self):
        return self.__str__()
 
