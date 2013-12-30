#!/usr/bin/Rscript
args <- commandArgs(TRUE);
require(ggplot2)

PR <- read.table(args[1],sep=',',header=T)
OUTFILE <- args[2]
TITLE <- args[3]

png(OUTFILE,height=400,width=400)
print(ggplot(data=PR,aes(x=recall,y=precision,group=rank,color=rank)) + geom_line() + ggtitle(TITLE))
dev.off()

