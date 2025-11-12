# Task completion checklist
- Re-run relevant `bfcl` generation/evaluation commands for any categories/models touched, or at least sanity-check via targeted `bfcl evaluate --partial-eval` on modified outputs.
- Execute pytest suites covering edited modules (e.g., `pytest bfcl_eval/...`), or explain why tests were skipped.
- Ensure new handlers/config updates are wired into `bfcl_eval/constants/model_config.py` and documented (README/SUPPORTED_MODELS) if applicable.
- Verify artifacts land under the expected `BFCL_PROJECT_ROOT` subdirectories (`result/`, `score/`), no hard-coded paths.
- Summarize code changes and next steps for the user; mention any manual follow-ups (API keys, env vars, regen data) still required.