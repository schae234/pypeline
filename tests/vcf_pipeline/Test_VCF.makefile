# -*- mode: Yaml; -*-
# Timestamp: %s

Options:
# Options for the pipeline
    Pileup: samtools
    Genotyper: bcftools
    Binary: False 

Prefixes:
    Test_Fasta:
        Path: 000_Indices/rCRS.fasta
        Label: Test_Fasta_File

Targets:
      - Group: Grouping 1
        Bams:
            - Test_1.Test_Fasta.realigned.bam
            - Test_2.Test_Fasta.realigned.bam
      - Group: Grouping 2
        Bams:
            - Test_1.Test_Fasta.realigned.bam
            - Test_2.Test_Fasta.realigned.bam 
