---
name: run-pipeline
description: Run the multi-agent banking pipeline end-to-end and report the results from shared/results/.
---

# /run-pipeline — Run the full banking pipeline

Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `sample-transactions.json` exists in the project root. If missing, stop and say so.
2. Clear the `shared/` working directories so the run starts clean:
   `rm -f shared/input/*.json shared/processing/*.json shared/output/*.json shared/results/*.json`
3. Run the pipeline: `python3 integrator.py`
4. Show a summary of results from `shared/results/`: read `shared/results/_summary.json` and report
   the tally (total / validated / rejected / flagged / settled).
5. Report any transactions that were **rejected** and why (transaction_id + reason), and any that were
   **flagged** for review (transaction_id + risk_level + risk_reasons).
