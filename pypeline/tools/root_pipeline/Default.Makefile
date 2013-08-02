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
# Fasta Sequence References
    Test_Fasta:
        Path: 000_Indices/ZmB73_5a_RefGen_v2.fa
        Label: Test_Fasta_File

# This pipeline follows the NCBI SRA archive format for handling
# data relationships. 

# A collection of studies which are examined collectively
Pipeline:
    Title: Root Ionomic Network
    Accession: 000_RawReads
    # A Set of experiments, overall goal
    Studies: # (SRP000000)
        # Consistent set of lab operations on input material (samples) w/ expected results
      - Title: "Zeanome"
        Submitter: Iowa State Univ.
        Accession: SRP011480
        Experiments: # (SRX000000)
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Tzi8 seedling root RNA-Seq"
             Accession: SRX129813
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Tzi8
                Accession: SRS300579
                Runs: # (SRR000000)
                    - SRR445655.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Tx303 seedling root RNA-Seq"
             Accession: SRX129809
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Tx303
                Accession: SRS300578
                Runs: # (SRR000000)
                    - SRR445651.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. P39 seedling root RNA-Seq"
             Accession: SRX129805
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: P39
                Accession: SRS300577
                Runs: # (SRR000000)
                    - SRR445647.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Oh7B seedling root RNA-Seq"
             Accession: SRX129801
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Oh7B
                Accession: SRS300576
                Runs: # (SRR000000)
                    - SRR445643.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Oh43 seedling root RNA-Seq"
             Accession: SRX129797
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Oh43
                Accession: SRS300575
                Runs: # (SRR000000)
                    - SRR445639.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. NC358 seedling root RNA-Seq"
             Accession: SRX129793
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: NC358
                Accession: SRS300574
                Runs: # (SRR000000)
                    - SRR445632.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. NC350 seedling root RNA-Seq"
             Accession: SRX129789
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: NC350
                Accession: SRS300573
                Runs: # (SRR000000)
                    - SRR445627.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Ms71 seedling root RNA-Seq"
             Accession: SRX129786
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Ms71
                Accession: SRS300572
                Runs: # (SRR000000)
                    - SRR445624.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Mo17 seedling root RNA-Seq"
             Accession: SRX129776
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Mo17
                Accession: SRS300568
                Runs: # (SRR000000)
                    - SRR445616.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. M37W seedling root RNA-Seq"
             Accession: SRX129771
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: M37W
                Accession: SRS300566
                Runs: # (SRR000000)
                    - SRR445583.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. M162W seedling root RNA-Seq"
             Accession: SRX129767
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: M162W
                Accession: SRS300564
                Runs: # (SRR000000)
                    - SRR445531.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Ky21 seedling root RNA-Seq"
             Accession: SRX129760
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Ky21
                Accession: SRS300561
                Runs: # (SRR000000)
                    - SRR445452.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Ki3 seedling root RNA-Seq"
             Accession: SRX129755
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Ki3
                Accession: SRS300559
                Runs: # (SRR000000)
                    - SRR445434.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Ki11 seedling root RNA-Seq"
             Accession: SRX129751
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Ki11
                Accession: SRS300558
                Runs: # (SRR000000)
                    - SRR445429.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: " Zea mays ssp. mays L. IL14H seedling root RNA-Seq"
             Accession: SRX129747
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: IL14H
                Accession: SRS300557
                Runs: # (SRR000000)
                    - SRR445425.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. Hp301 seedling root RNA-Seq"
             Accession: SRX129743
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Hp301
                Accession: SRS300556
                Runs: # (SRR000000)
                    - SRR445421.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. CML69 seedling root RNA-Seq"
             Accession: SRX129735
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: CML69
                Accession: SRS300551
                Runs: # (SRR000000)
                    - SRR445417.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. CML52 seedling root RNA-Seq"
             Accession: SRX129731
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: CML52
                Accession: SRS300550
                Runs: # (SRR000000)
                    - SRR445413.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. CML333 seedling root RNA-Seq"
             Accession: SRX129727
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: CML333
                Accession: SRS300549
                Runs: # (SRR000000)
                    - SRR445409.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "Zea mays ssp. mays L. CML322 seedling root RNA-Seq"
             Accession: SRX129723
             Instrument: Illumina HiSeq 2000
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: CML322
                Accession: SRS300548
                Runs: # (SRR000000)
                    - SRR445405.sra
        # Consistent set of lab operations on input material (samples) w/ expected results
      - Title: "GSE43142: Conservation and Divergence of Transcriptomic and Epigenomic Variations in Maize Hybrids"
        Submitter: "GEO Series/gds:200043142"
        Accession: SRP017685
        Experiments: # (SRX000000)
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1057293: mRNA-seq_Mo17/B73_root; Zea mays; RNA-Seq"
             Accession: SRX212604
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Mo17/B73
                Accession: SRS381462
                Runs: # (SRR000000)
                    - SRR640270.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1057291: mRNA-seq_B73/Mo17_root; Zea mays; RNA-Seq"
             Accession: SRX212602
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: B73/Mo17
                Accession: SRS381460
                Runs: # (SRR000000)
                    - SRR640268.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1057289: mRNA-seq_Mo17_root; Zea mays; RNA-Seq"
             Accession: SRX212600
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: Mo17
                    Accession: SRS381458
                Runs: # (SRR000000)
                    - SRR640266.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1057287: mRNA-seq_B73_root; Zea mays; RNA-Seq"
             Accession: SRX212598
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: B73
                Accession: SRS381456
                Runs: # (SRR000000)
                    - SRR640264.sra
        # Consistent set of lab operations on input material (samples) w/ expected results
      - Title: "GSE40952: Digital gene expression analysis of early root infection of Sporisorium reilianum f.sp.zeae in maize based on susceptible and resistant lines"
        Submitter: GEO Series/gds:200040952 
        Accession: SRP015787
        Experiments: # (SRX000000)
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005511: M-P2; Zea mays; RNA-Seq"
             Accession: SRX187574
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: M-P2
                Accession: SRS363933
                Runs: # (SRR000000)
                    - SRR572427.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005510: M-P1; Zea mays; RNA-Seq"
             Accession: SRX187573
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: M-P1
                Accession: SRS363932
                Runs: # (SRR000000)
                    - SRR572426.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005509: M-CK; Zea mays; RNA-Seq"
             Accession: SRX187572
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: M-CK
                Accession: SRS363931
                Runs: # (SRR000000)
                    - SRR572425.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005508: H-P2; Zea mays; RNA-Seq"
             Accession: SRX187571
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: H-P2
                Accession: SRS363930
                Runs: # (SRR000000)
                    - SRR572424.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005506: H-CK; Zea mays; RNA-Seq"
             Accession: SRX187569
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: H-CK
                Accession: SRS363928
                Runs: # (SRR000000)
                    - SRR572422.sra
             # Expressed in terms of individual samples or bundles of samples
           - Title: "GSM1005507: H-P1; Zea mays; RNA-Seq"
             Accession: SRX187570
             Instrument: Illumina Genome Analyzer
             Samples: # (SRS000000)
                # Results of machine runs. Comprised of data gathered for a sample, referring to a defining experiment
                Title: H-P1
                Accession: SRS363929
                Runs: # (SRR000000)
                    - SRR572423.sra




















