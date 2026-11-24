# Registered historical Chinese enterprise-text comparison

English reading copy; the [original registration](https://github.com/123yjf/pyjev_ai_security/tree/b2530fab3029bedd0b0cd8a42d1686ca7bd0c0af/research/enterprise/PROTOCOL.md) and sealed artifacts determine the historical experiment. Public text auditing only: no gateway, tools, paid inference or customer traffic.

1. Freeze the predecessor and the [HikmaAI INT8 ONNX revision](https://huggingface.co/HikmaAI/hikmaai-mdeberta-v3-base-prompt-injection/tree/b7d8317a617012d23713f4999acaba0690bc1c73). Verify class polarity on 16 fixed controls from each published class without tuning. Score at 0.5; report 0.005 as a separate sensitivity analysis.
2. Use unchanged Chinese documents and direct questions from the pinned Horizon-Labs synthetic test configurations. Require both language labels to match. The primary business-document subset was selected by predeclared topics; also report the full subsets. Texts may share templates.
3. From agent-safety-bench-zh use the supplied context only for benign and prompt-injection records; omit destructive-action records because danger does not imply injection. Compare scene labels, not executed tool actions.
4. Keep provider binary labels. One reviewer separately codes benign risk discussions and quoted design examples before inference. Remove normalized exact matches and prior overlaps using 5-character shingle Jaccard at 0.70; keep and report within-set near pairs. Undisclosed training overlap cannot be fully excluded.
5. Keep input and gold separate. Seal opaque identifiers and texts before prediction, seal predictions before scoring. Use 510 content tokens per window, overlap 64, maximum score, batch one; do not silently truncate. Report misses, false alarms, abstentions and paired errors by stratum. Do not estimate production prevalence or significance from templated samples.

[Source catalog](sources.json) · [Input seal](cohort.json) · [Prediction seal](prediction-receipt.json) · [Historical results](../../docs/enterprise-blind.md)
