# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 5b out of 5b
- Commentary: The submission is thorough and well-structured across all four tasks. Task 1 selects three distinct, valid prompting frameworks (RACE, RTF, CO-STAR) from frompting.com, correctly avoiding ROSES and zero-shot, with each prompt file containing the schema, questions, and rationale. Task 2 produces genuine SQL outputs from a real model run, measures inference times, computes accuracy, and includes a visualization script and an adapted evaluator that compares restaurant names while ignoring IDs. Task 3 proposes F1-score as an original partial-match metric, implements it in f1.py, and reports per-prompt averages. Task 4 delivers a detailed report with comparison tables, statistical significance testing (McNemar, Wilcoxon, Holm correction), p-values, and a multi-panel chart. Outputs are consistent, code is functional, and all deliverables are present and documented.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: The student selected three prompting frameworks from frompting.com: RACE, RTF, and CO-STAR. All are explicitly distinct from ROSES and zero-shot as required. Each framework has a dedicated prompt file (promptRACE.txt, promptRTF.txt, promptCOSTAR.txt) that includes the framework structure, the full database schema, the embedded test questions, and instructions to use only the question column. Task_1.md provides the source URLs and a rationale for each choice (in Slovak). All required outputs are present.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: The student used the three prompts to generate SQL query outputs (RACEout.txt, RTFout.txt, COSTARout.txt), ran each in a separate session, and measured inference times (RACE 3m12s, RTF 2m32s, CO-STAR 2m35s). Accuracy was computed using an adapted evaluator that compares predicted restaurant-name multisets against labels while ignoring IDs: RACE 135/155 (87.10%), RTF 127/155 (81.94%), CO-STAR 136/155 (87.74%). A vizualization script (task2_graph.py) generates Task_2_results.svg, and Task_2.md provides the comparison report.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposed F1-score (macro-averaged per question) as a new metric that captures partially correct predictions — true positives, false positives, and false negatives are computed at the restaurant-name level. This complements the all-or-nothing exact-match metric from Task 2 by rewarding partial correctness. The metric is implemented in f1.py, handles the empty-vs-empty edge case as F1 = 100%, and reports per-prompt averages: RACE 96.76%, RTF 90.02%, CO-STAR 95.30%.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: The student produced a detailed analysis with comparison tables spanning exact-match accuracy, macro-F1, and generation time. Statistical significance was assessed with McNemar's test (exact match) and pairwise Wilcoxon signed-rank test (F1), with Holm correction for the three pairwise comparisons. Adjusted p-values: RACE–RTF F1 p=0.004 (significant), RACE–CO-STAR not significant, RTF–CO-STAR F1 p=0.011 (significant); no exact-match comparison was statistically significant. task4_graph.py generates Task_4_results.svg with grouped bar charts, and Task_4.md includes the tables, p-values, and interpretation tying differences to the prompts, model, and coding agent.
