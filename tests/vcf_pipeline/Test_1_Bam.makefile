# -*- mode: Yaml; -*-
# Timestamp: 2013-07-16T16:46:41.698931
#
# Default options.
# Can also be specific for a set of samples, libraries, and lanes,
# by including the "Options" hierarchy at the same level as those
# samples, libraries, or lanes below. This does not include
# "Features", which may only be specific globally.
Options:
  # Sequencing platform, see SAM/BAM reference for valid values
  Platform: Illumina
  # Quality offset for PHRED scores, either 33 (Sanger/Illumina 1.8+) or 64 (Illumina 1.3+ / 1.5+)
  # For Bowtie2 it is also possible to specify 'Solexa', to handle reads on the Solexa scale.
  # This is used during adapter-trimming (AdapterRemoval) and sequence alignment (BWA/Bowtie2)
  QualityOffset: 33
  # Split a lane into multiple entries, one for each (pair of) file(s) found using the search-
  # string specified for a given lane. Each lane is named by adding a number to the end of the
  # given barcode.
  SplitLanesByFilenames: yes
  # Compression format used when storing FASTQ files (either 'gz' for GZip or 'bz2' for BZip2)
  CompressionFormat: bz2


  # Settings for aligners supported by the pipeline
  AdapterRemoval:
    # Which version of AdapterRemoval to use ('v1.4' or 'v1.5+')
    Version: 'v1.5+'

  Aligners:
    # Choice of aligner software to use, either "BWA" or "Bowtie2"
    Program: BWA

    # Settings for mappings performed using BWA
    BWA:
      # Filter hits with a mapping quality (PHRED) below this value
      MinQuality: 0
      # Should be disabled ("no") for aDNA alignments, as post-mortem localizes
      # to the seed region, which BWA expects to have few errors. Sets "-l".
      # See Schubert et al. 2012: http://pmid.us/22574660
      UseSeed:    yes
      # Additional command-line options may be specified for the "aln" call(s), as
      # described below for Bowtie2.

  # Filter PCR duplicates
  # Collapsed reads are filtered using Martin Kirchers FilterUnique,
  # while other reads are filtered using Picard MarkDuplicates.
  PCRDuplicates: yes
  # Carry out quality base re-scaling using mapDamage (*EXPERIMENTAL*)
  RescaleQualities: no

  # Exclude any type of trimmed reads from alignment/analysis
  # All reads are processed by default.
#  ExcludeReads:
#    - Single    # Single-ended reads, or PE reads where one mate was discarded
#    - Paired    # Pair-ended reads, where both reads were retained
#    - Collapsed # Overlapping pair-ended mate reads collapsed into a single read
#    - CollapsedTruncated # Like 'Collapsed', except that the reads have been
#                           truncated due to the presence of low quality bases.
#                           AdapterRemoval 1.5+ only.

  # Optional steps to perform during processing
  # To disable all features, replace with line "Features: []"
  Features:
#    - Raw BAM        # Generate BAM from the raw libraries (no indel realignment)
                     #   Location: {Destination}/{Target}.{Genome}.bam
    - Realigned BAM  # Generate indel-realigned BAM using the GATK Indel realigner
                     #   Location: {Destination}/{Target}.{Genome}.realigned.bam
#    - mapDamage      # Generate mapDamage plot for each (unrealigned) library
                     #   Location: {Destination}/{Target}.{Genome}.mapDamage/{Library}/
    - Coverage       # Generate coverage information for the raw BAM (wo/ indel realignment)
                     #   Location: {Destination}/{Target}.{Genome}.coverage
#    - Depths         # Generate histogram of number of sites with a given read-depth
                     #   Location: {Destination}/{Target}.{Genome}.depths
    - Summary        # Generate target summary (uses statistics from raw BAM)
                     #   Location: {Destination}/{Target}.summary


# Map of prefixes by name, each having a Path key, which specifies the location
# of the BWA/Bowtie2 index. This path should also be the filename of the
# reference FASTA sequence, such as is the case then a index is built using
# "bwa index PATH", in which case PATH would be PATH_TO_PREFIX below.
# At least ONE prefix must be specified!
#
# One or more areas of interest (for example the exome) may be specified using
# 'AreasOfInterest': Each area has a name, and points to a bedfile containing
# the relevant regions of the genome. Depths and coverage are calculated for
# these, merged by the name of the feature specified in the BED file. If no
# names are given in the BED file, the intervals are merged by contig, and
# named after the contig with a wildcard ("*") appended.
Prefixes:
  Test_Fasta:
    Path: 000_Indices/rCRS.fasta
    Label: nuclear
# of the BWA/Bowtie2 index. See the 'README.md' file for more information,
# Prefixes:
#  NAME_OF_PREFIX:
#    Path: PATH_TO_PREFIX
#    Label: # "mitochondrial" or "nuclear"
#    AreasOfInterest:
#      NAME: PATH_TO_BEDFILE


# Targets are specified using the following structure:
# NAME_OF_TARGET:
#   NAME_OF_SAMPLE:
#     NAME_OF_LIBRARY:
#       NAME_OF_LANE: PATH_WITH_WILDCARDS
Test_1:
    Test_1:
        GATCAG:
            Test_1: 000_RawReads/pe_reads_R{Pair}_001.fastq.gz
