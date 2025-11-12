# Code style & conventions
- Predominantly Python; type hints + docstrings used throughout (see `bfcl_eval/model_handler/base_handler.py`). Follow standard PEP 8 spacing/naming; classes/methods use lowercase_with_underscores, constants UPPER_CASE.
- Handlers inherit from `BaseHandler`; API vs local models split into FC vs prompting implementations (suffix `_FC` vs `_prompting`).
- Configuration/constants centralized under `bfcl_eval/constants/*`; prefer adding new enums/config entries there rather than scattering literals.
- CLI built with `typer`; new commands/options should follow existing Typer callback patterns.
- Datasets and logs use JSON; keep schema compatible with existing `result/` & `score/` structure. Use `dataclasses`/`pydantic` models when extending structured configs.
- Tests (where present) rely on `pytest`; fixtures live under `bfcl_eval/eval_checker/multi_turn_eval/func_source_code/tests`. Keep new tests deterministic (no network).