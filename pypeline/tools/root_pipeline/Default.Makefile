# -*- mode: Yaml; -*-
# Timestamp: %s

Options:
# Options for the pipeline
    # Format raw reads are stored in
    ReadFormat: SRA # fastq
    Platform: Illumina
    Genotyper: bcftools
    Binary: False 

References:

    Test_Fasta:
        Path: 000_Indices/rCRS.fasta
        Label: Test_Fasta_File

Targets:

     - Goup: Test
       Bams:
            - Test_1.Test_Fasta.realigned.bam
            - Test_2.Test_Fasta.realigned.bam
