# Gorilla repo overview
- Monorepo hosting multiple UC Berkeley agentic/LLM projects (Gorilla API models, Berkeley Function Calling Leaderboard, Agent Arena, GoEx execution engine, RAFT, etc.).
- Most active development for BFCL (under `berkeley-function-call-leaderboard/`), a Python 3.10+ package (`bfcl_eval`) that evaluates function-calling/tool-calling abilities of LLMs (API hosted or local OSS) for agentic workflows (multi-turn web search, memory, format sensitivity, etc.).
- Key directories:
  - `berkeley-function-call-leaderboard/bfcl_eval`: CLI + evaluation pipeline (constants, model handlers for API/local models, eval checkers, datasets, scripts).
  - `agent-arena`: evaluation assets for Gorilla X LMSYS Agent Arena.
  - `goex`: Gorilla execution engine for running/validating LLM-issued actions.
  - `raft`: RAG adaptation tooling/data.
- `bfcl_eval` installs as a CLI (`bfcl`) for generation/evaluation; stores run artifacts in `result/` and `score/` (configurable via `BFCL_PROJECT_ROOT`).