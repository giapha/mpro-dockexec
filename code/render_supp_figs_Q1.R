#!/usr/bin/env Rscript
# Supplementary figures (Q1, same theme as main).
# SF2: method-fix effect — median |D| by class, v1 (default 25A box) vs v2 (reported box).
# SF3: bootstrap sampling distribution of E3 vs E2 median |D| (shows CI overlap, P=0.14).
suppressPackageStartupMessages({library(ggplot2);library(patchwork)})
H<-"/Users/GiapHa/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault/Vincent/Job/NewScience-Cofounder/Paper1_Audit"
FIG<-file.path(H,"08_manuscript_v0.3/figures")
rd<-function(p){r<-read.csv(p,stringsAsFactors=F);r<-r[r$rerun_score!="" & !is.na(suppressWarnings(as.numeric(r$rerun_score))),];r$rerun_score<-as.numeric(r$rerun_score);r$abs_delta<-abs(as.numeric(r$abs_delta));r[r$rerun_score<=-2,]}
v2<-rd(file.path(H,"09_scoring_benchmark/runner/out/reproduction_outcomes.csv"))
v1<-rd(file.path(H,"09_scoring_benchmark/runner/out/reproduction_outcomes_v1_default25.csv"))
med<-function(d,e) median(d$abs_delta[d$e_class==e]); medall<-function(d) median(d$abs_delta)
base<-theme_classic(base_size=12)+theme(plot.title=element_text(face="bold",size=13),
  axis.title=element_text(size=11.5),axis.text=element_text(size=10,colour="grey20"),
  legend.title=element_blank(),legend.position=c(0.85,0.9),plot.tag=element_text(face="bold",size=16))
PAL<-c("v1 (default 25 A box)"="#bdbdbd","v2 (reported box)"="#1b7837")

## SF2 — method-fix bars
dS<-data.frame(
  stratum=factor(rep(c("E3","E2","All"),2),levels=c("E3","E2","All")),
  run=rep(c("v1 (default 25 A box)","v2 (reported box)"),each=3),
  val=c(med(v1,"E3"),med(v1,"E2"),medall(v1),med(v2,"E3"),med(v2,"E2"),medall(v2)))
pA<-ggplot(dS,aes(stratum,val,fill=run))+
  geom_col(position=position_dodge(0.7),width=0.62,colour="black",linewidth=0.2)+
  geom_text(aes(label=sprintf("%.2f",val)),position=position_dodge(0.7),vjust=-0.4,size=3,colour="grey15")+
  scale_fill_manual(values=PAL)+scale_y_continuous(expand=expansion(mult=c(0,0.15)))+
  labs(title="Method fix: reported box tightens reproduction",x=NULL,y="median |delta| (kcal/mol)")+base

## SF3 — bootstrap median distributions
set.seed(2026)
boot<-function(x,n=4000) replicate(n, median(sample(x,length(x),replace=TRUE)))
e3<-v2$abs_delta[v2$e_class=="E3"]; e2<-v2$abs_delta[v2$e_class=="E2"]
dB<-rbind(data.frame(cls="E3 (n=6)",v=boot(e3)),data.frame(cls="E2 (n=31)",v=boot(e2)))
pB<-ggplot(dB,aes(v,fill=cls))+geom_density(alpha=0.5,colour=NA)+
  geom_vline(xintercept=median(e3),colour="#1b7837",linetype="dashed")+
  geom_vline(xintercept=median(e2),colour="#E08214",linetype="dashed")+
  scale_fill_manual(values=c("E3 (n=6)"="#1b7837","E2 (n=31)"="#E08214"))+
  labs(title="Bootstrap median distributions overlap (Mann-Whitney P=0.14)",
       x="bootstrap median |delta| (kcal/mol)",y="density")+
  base+theme(legend.position=c(0.82,0.85))
ggsave(file.path(FIG,"FigureS2_method_fix_v1_v2.png"),pA,width=7.2,height=4.6,dpi=320,bg="white")
ggsave(file.path(FIG,"FigureS3_bootstrap_overlap.png"),pB,width=7.2,height=4.6,dpi=320,bg="white")
cat("wrote FigureS2_method_fix_v1_v2.png, FigureS3_bootstrap_overlap.png\n")
cat(sprintf("v1 E3 %.2f E2 %.2f | v2 E3 %.2f E2 %.2f\n",med(v1,"E3"),med(v1,"E2"),med(v2,"E3"),med(v2,"E2")))
