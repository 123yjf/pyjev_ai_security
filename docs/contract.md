# Compatibility API contract

For **pyjev_v1**, use the [current CLI, Python API and field reference](start-local.md#examples). This page documents the separate `pyjev` interface for existing integrations.

## Inputs

`audit(text)` takes one authorized, nonblank Unicode string of at most 32,768 characters, without isolated surrogates. Text is never interpreted as a URL, credential or tool command. `scan -` reads one full text from stdin; `batch` reads one UTF-8 JSON object with a single string `text` field per line. A plain pipe into `pyjev` processes one raw text per line, not JSONL. The batch-line and scan transport cap is 256 KiB. Duplicate JSON keys are errors. Use only nonsensitive synthetic inputs in command-line arguments.

## Outputs

The immutable audit object and `--json` follow the [compatibility JSON schema](audit.schema.json). `review` is the conservative suggestion; `experimental_review` is a comparison field, not a tool decision. A suspected mention can have `review=review` and `experimental_review=record_only`. A non-analyzable text has `signal=unknown` and `review=incomplete`. `speech_act=unclear` is a valid intent label and does not alone mean the input is invalid.

`execution_evidence=not_observed`, `grants_authority=false` and `service_action=none` apply to this program only. Do not infer that another client took no action. A failed artifact checksum raises `ModelIntegrityError`; do not substitute a negative audit.

## Batch operations

Each output is `{"line":1,"audit":{...}}` or a line number and an error code. Bad lines do not echo their input or suppress subsequent valid lines. Exit `0` means processing completed, including flagged or incomplete audit records; `1` is an integrity/check failure, `2` a CLI, encoding or transport error, and `130` an interruption. These codes belong to this interface; the [named auditor](start-local.md) reports non-analyzable input with exit code 2.
