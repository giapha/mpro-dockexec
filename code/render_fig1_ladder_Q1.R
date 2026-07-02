#!/usr/bin/env Rscript
# Figure 1 (Q1 concept) — 16 MERS-Dock fields by tier -> deterministic rule -> E0-E4 ladder.
# Uses the canonical project palettes so the whole figure set is colour-coherent:
#   E-class: E1 red, E2 amber, E3 green, E4 blue (same as Fig 3/4/5)
#   Tier:    purple sequence (distinct from E-class; same as Fig 2)
# ASCII-safe labels (macOS tofu memory).
suppressPackageStartupMessages({ library(ggplot2) })
FIG <- "/Users/GiapHa/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault/Vincent/Job/NewScience-Cofounder/Paper1_Audit/08_manuscript_v0.3/figures"
TIER <- c("#762a83", "#9970ab", "#c2a5cf")          # T1 dark -> T3 light purple
ECL  <- c(E1="#d73027", E2="#E08214", E3="#1b7837", E4="#4575b4")

box <- function(xmin,xmax,ymin,ymax,fill) data.frame(xmin,xmax,ymin,ymax,fill)
tiers <- rbind(
  cbind(box(0.2,4.5,6.7,9.3,TIER[1]), tier="TIER-1  execution-blocking",
        body="PDB/receptor . box centre . box size\ndocking software . ligand identity", rule="missing ANY  ->  E1", dark=TRUE),
  cbind(box(0.2,4.5,3.5,6.1,TIER[2]), tier="TIER-2  assumption-forcing",
        body="version . search effort . receptor prep\nligand prep . protonation . water/ion . chain", rule="missing  ->  E2 (needs assumptions)", dark=FALSE),
  cbind(box(0.2,4.5,0.3,2.9,TIER[3]), tier="TIER-3  robustness",
        body="random seed . validation/redocking\nreusable config", rule="all present  ->  E4", dark=FALSE))

lad <- rbind(
  cbind(box(6.3,9.8,7.7,9.1,ECL["E4"]), lab="E4", desc="fully reproducible", dark=TRUE),
  cbind(box(6.3,9.8,5.6,7.0,ECL["E3"]), lab="E3", desc="directly executable", dark=TRUE),
  cbind(box(6.3,9.8,3.5,4.9,ECL["E2"]), lab="E2", desc="needs assumptions", dark=FALSE),
  cbind(box(6.3,9.8,1.4,2.8,ECL["E1"]), lab="E1", desc="blocked", dark=TRUE))

p <- ggplot() +
  # tier boxes
  geom_rect(data=tiers, aes(xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax), fill=tiers$fill, colour="grey20", linewidth=0.3) +
  geom_text(data=tiers, aes(x=0.45, y=ymax-0.32, label=tier), hjust=0, fontface="bold", size=3.7,
            colour=ifelse(tiers$dark,"white","grey10")) +
  geom_text(data=tiers, aes(x=0.45, y=(ymin+ymax)/2-0.05, label=body), hjust=0, size=2.7, lineheight=0.95,
            colour=ifelse(tiers$dark,"grey90","grey20")) +
  geom_text(data=tiers, aes(x=0.45, y=ymin+0.3, label=rule), hjust=0, fontface="italic", size=2.7,
            colour=ifelse(tiers$dark,"grey85","grey25")) +
  # arrow
  annotate("segment", x=4.8, xend=6.1, y=5.0, yend=5.0, linewidth=0.9, colour="grey30",
           arrow=grid::arrow(length=unit(0.18,"cm"), type="closed")) +
  annotate("text", x=5.45, y=5.35, label="deterministic\nrule", size=2.8, colour="grey30", lineheight=0.9) +
  # ladder boxes
  geom_rect(data=lad, aes(xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax), fill=lad$fill, colour="grey20", linewidth=0.3) +
  geom_text(data=lad, aes(x=6.6, y=(ymin+ymax)/2, label=lab), hjust=0, fontface="bold", size=5,
            colour=ifelse(lad$dark,"white","grey10")) +
  geom_text(data=lad, aes(x=7.5, y=(ymin+ymax)/2, label=desc), hjust=0, size=3.4,
            colour=ifelse(lad$dark,"grey95","grey15")) +
  coord_cartesian(xlim=c(0,9.9), ylim=c(0,9.7), expand=FALSE) +
  labs(title="MERS-Dock: 16 fields by tier  ->  deterministic rule  ->  E1-E4 executability ladder") +
  theme_void(base_size=12) + theme(plot.title=element_text(face="bold", size=12.5, hjust=0.5, margin=margin(b=6)),
                                    plot.margin=margin(8,8,8,8))
ggsave(file.path(FIG,"Figure1_tier_ladder_Q1.png"), p, width=9.4, height=5.0, dpi=320, bg="white")
cat("wrote Figure1_tier_ladder_Q1.png\n")
