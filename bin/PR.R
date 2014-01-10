#!/usr/bin/Rscript
args <- commandArgs(TRUE);
require(ggplot2)

PR <- read.table(args[1],sep=',',header=T)
OUTFILE <- args[2]
TITLE <- args[3]
YLIM <- as.numeric(args[4])

ggsave(OUTFILE,ggplot(data=PR,aes(x=recall,y=precision,group=rank,color=rank)) + geom_line() + ggtitle(TITLE) + ylim(YLIM,1), width=7,height=5)

