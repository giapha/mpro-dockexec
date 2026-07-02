#!/usr/bin/env Rscript
# Figure 5 (Q1 composite) — re-execution: executability class predicts reproducibility.
# 4 panels: (A) reported vs re-executed scatter by E-class; (B) abs deviation by E-class
# (raincloud); (C) deviation vs Vina noise floor; (D) % within tolerance by stratum.
# ASCII-safe labels (macOS sans renders Unicode superscripts/minus as tofu — see memory).
suppressPackageStartupMessages({
  library(ggplot2); library(patchwork); library(ggdist); library(ggbeeswarm); library(scales)
})
HERE <- "/Users/GiapHa/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault/Vincent/Job/NewScience-Cofounder/Paper1_Audit"
OUT  <- file.path(HERE, "08_manuscript_v0.3/figures/Figure5_reexecution_Q1.png")
rep  <- read.csv(file.path(HERE, "09_scoring_benchmark/runner/out/reproduction_outcomes.csv"), stringsAsFactors = FALSE)
sc   <- read.csv(file.path(HERE, "09_scoring_benchmark/runner/out/self_consistency.csv"), stringsAsFactors = FALSE)

rep <- rep[rep$rerun_score != "" & !is.na(suppressWarnings(as.numeric(rep$rerun_score))), ]
rep$rerun_score   <- as.numeric(rep$rerun_score)
rep$reported_score<- as.numeric(rep$reported_score)
rep$abs_delta     <- abs(as.numeric(rep$abs_delta))
qc <- rep[rep$rerun_score <= -2.0, ]                 # QC: drop failed docks (locked N=39)
qc$Eclass <- factor(qc$e_class, levels = c("E3","E2"))

TOL <- 2.0
noise_med <- median(as.numeric(sc$range)); noise_max <- max(as.numeric(sc$range))
PAL <- c(E3 = "#1b7837", E2 = "#E08214")            # E3 = strong green (directly-exec), E2 = amber
band <- "#1b783722"

base <- theme_classic(base_size = 12) + theme(
  plot.title = element_text(face = "bold", size = 13),
  plot.subtitle = element_text(size = 9, colour = "grey45"),
  axis.title = element_text(size = 11.5), axis.text = element_text(size = 10, colour = "grey20"),
  legend.position = "none", plot.tag = element_text(face = "bold", size = 16),
  plot.margin = margin(8, 10, 6, 8))

med <- function(x) median(x, na.rm = TRUE)
wpct <- function(x, t) round(100 * mean(x <= t))

## Panel A — reported vs re-executed scatter
lim <- range(c(qc$reported_score, qc$rerun_score)); lim <- c(floor(lim[1]), ceiling(lim[2]))
pA <- ggplot(qc, aes(reported_score, rerun_score)) +
  geom_ribbon(data = data.frame(x = lim), aes(x = x, ymin = x - TOL, ymax = x + TOL),
              inherit.aes = FALSE, fill = "#1b7837", alpha = 0.08) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", linewidth = 0.5, colour = "grey40") +
  geom_point(aes(fill = Eclass, shape = Eclass), size = 2.9, colour = "black", stroke = 0.25, alpha = 0.92) +
  scale_fill_manual(values = PAL) + scale_shape_manual(values = c(E3 = 23, E2 = 21)) +
  coord_equal(xlim = lim, ylim = lim) +
  labs(title = "Reported vs re-executed", x = "reported score (kcal/mol)", y = "re-executed score (kcal/mol)") +
  annotate("text", x = lim[1] + 0.3, y = lim[2] - 0.2, hjust = 0, vjust = 1, size = 3.3, colour = "grey30",
           label = "dashed = identity\nband = +/- 2 kcal/mol") +
  guides(fill = guide_legend(override.aes = list(size = 3.2)), shape = "none") + base +
  theme(legend.position = c(0.84, 0.16), legend.title = element_blank(),
        legend.text = element_text(size = 9), legend.key.size = unit(0.9, "lines"),
        legend.background = element_rect(fill = "white", colour = "grey80", linewidth = 0.3))

## Panel B — abs deviation by E-class (raincloud)
labB <- data.frame(Eclass = factor(c("E3","E2"), levels = c("E3","E2")),
                   y = c(med(qc$abs_delta[qc$Eclass=="E3"]), med(qc$abs_delta[qc$Eclass=="E2"])))
labB$txt <- sprintf("median %.2f", labB$y)
pB <- ggplot(qc, aes(Eclass, abs_delta, fill = Eclass, colour = Eclass)) +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = 0, ymax = noise_max, fill = "grey85", alpha = 0.6) +
  stat_halfeye(adjust = 0.8, width = 0.55, .width = 0, justification = -0.18, alpha = 0.35, colour = NA) +
  geom_boxplot(width = 0.13, outlier.shape = NA, alpha = 0.5, colour = "grey25") +
  geom_quasirandom(width = 0.09, size = 2, shape = 21, colour = "black", stroke = 0.22) +
  geom_text(data = labB, aes(Eclass, y, label = txt), inherit.aes = FALSE,
            nudge_x = 0.34, vjust = -0.6, size = 3.2, fontface = "bold", colour = "grey15") +
  scale_fill_manual(values = PAL) + scale_colour_manual(values = PAL) +
  labs(title = "Deviation by executability class", x = NULL, y = "absolute deviation (kcal/mol)",
       subtitle = "grey band = Vina self-noise floor") + base

## Panel C — median deviation vs noise floor (lollipop)
dC <- data.frame(stratum = c("E3","E2","All"),
                 val = c(med(qc$abs_delta[qc$Eclass=="E3"]), med(qc$abs_delta[qc$Eclass=="E2"]), med(qc$abs_delta)))
dC$stratum <- factor(dC$stratum, levels = c("All","E2","E3"))
dC$col <- c("#1b7837","#E08214","grey35")[match(as.character(dC$stratum), c("E3","E2","All"))]
pC <- ggplot(dC, aes(val, stratum)) +
  annotate("rect", xmin = 0, xmax = noise_max, ymin = -Inf, ymax = Inf, fill = "grey85", alpha = 0.7) +
  geom_segment(aes(x = 0, xend = val, yend = stratum, colour = stratum), linewidth = 1.1) +
  geom_point(aes(colour = stratum), size = 4.2) +
  geom_text(aes(label = sprintf("%.2f", val)), vjust = -1.1, size = 3.2, fontface = "bold", colour = "grey15") +
  scale_colour_manual(values = c(All = "grey35", E2 = "#E08214", E3 = "#1b7837")) +
  scale_x_continuous(limits = c(0, max(dC$val) * 1.18), expand = expansion(mult = c(0, 0.02))) +
  labs(title = "Median deviation vs noise floor", x = "median absolute deviation (kcal/mol)", y = NULL,
       subtitle = sprintf("grey band = Vina noise (<= %.2f)", noise_max)) + base

## Panel D — % within tolerance by stratum
dD <- data.frame(
  stratum = c("E3","6Y2E","All","6LU7","E2"),
  pct = c(wpct(qc$abs_delta[qc$Eclass=="E3"], TOL),
          wpct(qc$abs_delta[qc$target_pdb=="6Y2E"], TOL),
          wpct(qc$abs_delta, TOL),
          wpct(qc$abs_delta[qc$target_pdb=="6LU7"], TOL),
          wpct(qc$abs_delta[qc$Eclass=="E2"], TOL)))
dD <- dD[order(dD$pct), ]; dD$stratum <- factor(dD$stratum, levels = dD$stratum)
dD$kind <- ifelse(dD$stratum %in% c("E3","E2"), as.character(dD$stratum), "other")
pD <- ggplot(dD, aes(pct, stratum, fill = kind)) +
  geom_col(width = 0.66, colour = "black", linewidth = 0.2) +
  geom_text(aes(label = paste0(pct, "%")), hjust = -0.18, size = 3.3, fontface = "bold", colour = "grey15") +
  scale_fill_manual(values = c(E3 = "#1b7837", E2 = "#E08214", other = "grey70")) +
  scale_x_continuous(limits = c(0, 112), breaks = c(0,25,50,75,100), expand = expansion(mult = c(0, 0))) +
  labs(title = "Reproduced within tolerance", x = "% within 2 kcal/mol", y = NULL) + base

fig <- (pA | pB) / (pC | pD) +
  plot_annotation(tag_levels = "A",
    title = "Executability class predicts reproducibility of docking scores",
    subtitle = sprintf("N=%d CID-anchored claims, 2 targets, AutoDock Vina 1.2.7; pre-registered tolerance %.1f kcal/mol; Vina self-noise median %.2f", nrow(qc), TOL, noise_med),
    theme = theme(plot.title = element_text(face = "bold", size = 15),
                  plot.subtitle = element_text(size = 10.5, colour = "grey35")))

ggsave(OUT, fig, width = 10.4, height = 9.2, dpi = 320, bg = "white")
cat("wrote", OUT, "\n")
cat(sprintf("QC N=%d | E3 n=%d med %.2f | E2 n=%d med %.2f | noise med %.2f max %.2f\n",
            nrow(qc), sum(qc$Eclass=="E3"), med(qc$abs_delta[qc$Eclass=="E3"]),
            sum(qc$Eclass=="E2"), med(qc$abs_delta[qc$Eclass=="E2"]), noise_med, noise_max))
