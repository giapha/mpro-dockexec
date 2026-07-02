#!/usr/bin/env Rscript
# Q1 rebuild of the audit figures (2 completeness, 3 field matrix, 4 E-distribution),
# matching the Figure-5 theme so the whole set is coherent. Numbers read from the
# locked data files (Table2_completeness_N236.csv, method_audit_scaled.csv,
# stats_relocked.json) — no transcription. ASCII-safe labels (macOS tofu memory).
suppressPackageStartupMessages({
  library(ggplot2); library(scales); library(jsonlite)
})
A   <- "/Users/GiapHa/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-vault/Vincent/Job/NewScience-Cofounder/Paper1_Audit/08_manuscript_v0.3"
FIG <- file.path(A, "figures")

PAL_TIER <- c("Tier-1 (blocks execution)" = "#762a83",
              "Tier-2 (forces assumptions)" = "#9970ab",
              "Tier-3 (robustness)" = "#c2a5cf",
              "Result" = "#525252")
base <- theme_classic(base_size = 12) + theme(
  plot.title = element_text(face = "bold", size = 14),
  plot.subtitle = element_text(size = 10, colour = "grey45"),
  axis.title = element_text(size = 11.5), axis.text = element_text(size = 10, colour = "grey20"),
  legend.title = element_blank(), legend.text = element_text(size = 9.5),
  plot.margin = margin(10, 14, 8, 10))

## ---------------- Figure 2 — reporting completeness ----------------
comp <- read.csv(file.path(A, "analysis/Table2_completeness_N236.csv"), stringsAsFactors = FALSE)
ci <- do.call(rbind, lapply(strsplit(comp$wilson95, "-"), as.numeric))
comp$lo <- ci[, 1]; comp$hi <- ci[, 2]
tier1 <- c("PDB/receptor","Grid centre","Grid size","Docking software","Ligand identifier")
tier2 <- c("Software version","Search effort","Receptor preparation","Ligand preparation","Protonation/tautomer","Water/ion handling","Protein chain")
tier3 <- c("Random seed","Validation/redocking","Reusable code/config")
comp$tier <- ifelse(comp$field %in% tier1, "Tier-1 (blocks execution)",
              ifelse(comp$field %in% tier2, "Tier-2 (forces assumptions)",
              ifelse(comp$field %in% tier3, "Tier-3 (robustness)", "Result")))
comp$field <- factor(comp$field, levels = comp$field[order(comp$pct_reported)])
p2 <- ggplot(comp, aes(pct_reported, field, fill = tier)) +
  geom_col(width = 0.7, colour = "black", linewidth = 0.2) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.28, colour = "grey25", linewidth = 0.4) +
  geom_text(aes(x = hi, label = sprintf("%.1f%%", pct_reported)), hjust = -0.3, size = 3.1, colour = "grey15") +
  scale_fill_manual(values = PAL_TIER) +
  scale_x_continuous(limits = c(0, 108), breaks = c(0,25,50,75,100), expand = expansion(mult = c(0,0))) +
  labs(title = "Reporting completeness across the 16 MERS-Dock fields",
       subtitle = "N = 236 papers; bars = % reported (strict), whiskers = Wilson 95% CI",
       x = "% of papers reporting the field", y = NULL) +
  base + theme(legend.position = c(0.74, 0.22),
               legend.background = element_rect(fill = "white", colour = "grey80", linewidth = 0.3))
ggsave(file.path(FIG, "Figure2_reporting_completeness_Q1.png"), p2, width = 8.6, height = 6.6, dpi = 320, bg = "white")

## ---------------- Figure 4 — executability distribution ----------------
st <- fromJSON(file.path(A, "analysis/stats_relocked.json"))
mk <- function(node, denom_label) {
  do.call(rbind, lapply(c("E1","E2","E3","E4"), function(k) {
    x <- node[[k]]
    data.frame(class = k, pct = x$pct,
               lo = if (!is.null(x$wilson95)) x$wilson95[1] else NA,
               hi = if (!is.null(x$wilson95)) x$wilson95[2] else NA,
               n = x$n, panel = denom_label)
  }))
}
d4 <- rbind(mk(st$paper_level_rule_relocked, "Paper-level (N = 236)"),
            mk(st$claim_weighted_rule, "Claim-weighted (~12,466 claims)"))
d4$panel <- factor(d4$panel, levels = c("Paper-level (N = 236)", "Claim-weighted (~12,466 claims)"))
PAL_E <- c(E1 = "#d73027", E2 = "#E08214", E3 = "#1b7837", E4 = "#4575b4")
d4$lab <- ifelse(is.na(d4$lo), sprintf("%.1f%%", d4$pct), sprintf("%d\n%.1f%%", d4$n, d4$pct))
p4 <- ggplot(d4, aes(class, pct, fill = class)) +
  geom_col(width = 0.72, colour = "black", linewidth = 0.2) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.22, colour = "grey25", linewidth = 0.4, na.rm = TRUE) +
  geom_text(aes(y = ifelse(is.na(hi), pct, hi), label = lab), vjust = -0.45, size = 3.1, colour = "grey15", lineheight = 0.85) +
  facet_wrap(~panel, scales = "free_y") +
  scale_fill_manual(values = PAL_E, guide = "none") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.18))) +
  labs(title = "Executability distribution (E1-E4)",
       subtitle = "Deterministic rule classifier (reproduces human R1 at kappa = 0.926)",
       x = NULL, y = "% ") +
  base + theme(strip.background = element_rect(fill = "grey95", colour = NA),
               strip.text = element_text(face = "bold", size = 11))
ggsave(file.path(FIG, "Figure4_executability_distribution_Q1.png"), p4, width = 9.0, height = 5.2, dpi = 320, bg = "white")

## ---------------- Figure 3 — per-paper field matrix (heatmap) ----------------
ok <- requireNamespace("ComplexHeatmap", quietly = TRUE) && requireNamespace("circlize", quietly = TRUE)
if (ok) {
  suppressPackageStartupMessages({ library(ComplexHeatmap); library(grid) })
  m <- read.csv(file.path(A, "analysis/method_audit_scaled.csv"), stringsAsFactors = FALSE)
  fld <- c(pdb_receptor="PDB/receptor", grid_center="Grid centre", grid_size="Grid size",
           docking_software="Docking software", ligand_identifier="Ligand identifier",
           software_version="Software version", search_effort="Search effort",
           receptor_preparation="Receptor prep", ligand_preparation="Ligand prep",
           protonation_tautomer="Protonation", water_ion_handling="Water/ion",
           protein_chain="Protein chain", random_seed="Random seed",
           validation_redocking="Validation", code_artifacts="Reusable config",
           numeric_result="Numeric result")
  fld <- fld[names(fld) %in% colnames(m)]
  mat <- t(as.matrix(m[, names(fld)]))                 # fields x papers
  rownames(mat) <- fld
  code <- function(v) ifelse(v == "reported", 2L, ifelse(v == "partial", 1L, 0L))
  matc <- apply(mat, 2, code); rownames(matc) <- fld
  ord <- order(factor(m$paper_e_class, levels = c("E1","E2","E3","E4")), -colSums(matc))
  matc <- matc[, ord]
  ecl <- m$paper_e_class[ord]
  col_fun <- c("0" = "#d73027", "1" = "#fec44f", "2" = "#2c7fb8")
  top <- HeatmapAnnotation(`E-class` = ecl,
            col = list(`E-class` = c(E1="#d73027", E2="#E08214", E3="#1b7837", E4="#4575b4")),
            annotation_name_gp = gpar(fontsize = 9), simple_anno_size = unit(4, "mm"),
            annotation_legend_param = list(`E-class` = list(title_gp = gpar(fontsize = 9, fontface = "bold"))))
  ht <- Heatmap(matrix(as.character(matc), nrow = nrow(matc), dimnames = dimnames(matc)),
          name = "field state",
          col = col_fun,
          top_annotation = top,
          cluster_rows = FALSE, cluster_columns = FALSE,
          show_column_names = FALSE,
          row_names_side = "left", row_names_gp = gpar(fontsize = 10),
          column_title = sprintf("236 papers (ordered by E-class, then completeness)  x  %d MERS-Dock fields", nrow(matc)),
          column_title_gp = gpar(fontsize = 11),
          heatmap_legend_param = list(at = c("2","1","0"), labels = c("reported","partial","missing"),
                                      title = "field state", title_gp = gpar(fontsize = 9, fontface = "bold"),
                                      labels_gp = gpar(fontsize = 9)),
          border = TRUE, rect_gp = gpar(col = NA))
  png(file.path(FIG, "Figure3_missing_parameter_matrix_Q1.png"), width = 9.6, height = 5.4, units = "in", res = 320, bg = "white")
  draw(ht, heatmap_legend_side = "right", annotation_legend_side = "right", merge_legend = TRUE)
  dev.off()
  cat("Fig3 heatmap OK\n")
} else cat("Fig3 SKIPPED (ComplexHeatmap/circlize missing)\n")

cat("wrote Figure2_reporting_completeness_Q1.png, Figure4_executability_distribution_Q1.png\n")
