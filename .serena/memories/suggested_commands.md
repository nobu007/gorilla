# Common commands
- Install BFCL dev env: `cd berkeley-function-call-leaderboard && pip install -e .` (optionally add extras: `pip install -e .[oss_eval_vllm]`, `.oss_eval_sglang`, `.wandb`).
- Set project root for artifacts: `export BFCL_PROJECT_ROOT=/path/to/workdir` (or use `.env`).
- Generate model responses (API models): `bfcl generate --model MODEL_NAME --test-category TEST_CATEGORY --num-threads 1 [--run-ids id1 id2 ...]`.
- Generate with local backend: `bfcl generate --model MODEL_NAME --test-category TEST_CATEGORY --backend {sglang|vllm} --num-gpus 1 --gpu-memory-utilization 0.9 [--local-model-path /models/foo]`.
- Use existing OpenAI-compatible endpoint: add `--skip-server-setup` and configure `LOCAL_SERVER_ENDPOINT` / `LOCAL_SERVER_PORT` in `.env`.
- Evaluate results: `bfcl evaluate --model MODEL_NAME --test-category TEST_CATEGORY [--partial-eval]`.
- Script alternative: `python -m bfcl_eval.openfunctions_evaluation ...` (generation) and `python -m bfcl_eval.eval_checker.eval_runner ...` (evaluation).
- Run unit tests (where available): `pytest bfcl_eval/eval_checker/multi_turn_eval/func_source_code/tests`. 