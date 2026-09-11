# AGENTS.md

Instructions for AI agents in this repo. Shared and version-controlled.

## Repo layout

A single Pulumi program that deploys RCTab to Azure. `Pulumi.yaml` points `main` at
`rctab_infrastructure/`, so `__main__.py` is the entrypoint: it wires up logging, then
the API webapp, function apps, database and key vault.

- `rctab_infrastructure/constants.py` — every stack config value, read once at import
  via `pulumi.Config`. Pulumi config keys are the lowercase form of the Python names.
- `rctab_infrastructure/utils.py` — validators and formatters used by `constants.py`.
- `rctab_infrastructure/{api,function_apps,database,keyvault,webapp,rctab_logging}.py` —
  one module per group of Azure resources.
- `tests/` — unit tests. `docs/` — Sphinx source; the deployment guide is
  `docs/content/deployment.md`.

## Commands

- Install: `poetry install --all-extras` (the `docs` extra is needed to build docs).
- Tests: `poetry run python -m unittest discover --verbose --start-directory tests`.
  This is what CI runs; there is no pytest dependency.
- Lint and format: `poetry run pre-commit run --all-files`.
- Docs: `poetry run make --directory docs html`.
- Pulumi: see the `pulumi` skill in `.claude/skills/` and `docs/content/deployment.md`.

## Style

Formatting and linting all run in pre-commit, and every hook is `language: system`
running under `poetry run` — so they need the project venv installed, and a bare
`black`/`pylint` will not match CI.

- Absolute imports only. `pylint` loads `pylint_absolute_imports` (see `.python-lint`),
  so a relative import fails the hook.
- `pyright` runs in `strict` mode over the whole repo (`pyrightconfig.json`). Annotate
  new functions fully; `Final[...]` on module-level constants.
- `pydocstyle --convention=google` applies to all Python files. Module, class and
  function docstrings are required even though `pylint` has the `missing-*-docstring`
  checks disabled — the two tools disagree, and `pydocstyle` is the binding one.
- `pymarkdownlnt --strict-config` runs on every markdown file, including this one and
  anything under `docs/`. Only MD013 (line length) is disabled in `.pymarkdown.json`,
  so blank lines around headings, lists and fenced blocks still matter.

## Repository conventions

- Adding a config value means three coordinated edits: a `config.get*`/`require*` line
  in `constants.py`, an entry in that module's `Attributes:` docstring (it is the
  reference the Sphinx docs render), and a section in `docs/content/deployment.md`
  under Required or Optional Config Variables.
- Secrets come back from `Config.get_secret`/`require_secret` as `Output[str]`, not
  `str`. Never interpolate one into an f-string — transform with `.apply(...)` and let
  Pulumi keep it encrypted in state.
- Validation belongs in `utils.py` and is applied at the point of reading the config in
  `constants.py`, so an invalid stack fails at `pulumi preview` rather than mid-deploy.
- Tests use `unittest`: `class ...(unittest.TestCase)` with `self.assert*`, and a short
  docstring per class. Follow `tests/test_utils.py` rather than introducing pytest.

## Tests

New features and fixes need tests. Pure helpers in `utils.py` are directly testable;
resource-constructing code needs `pulumi.runtime.set_mocks`, so prefer extracting the
logic worth testing into a helper over mocking the whole program.

## Boundaries

- `pulumi up` and `pulumi down` create, change and destroy real, billable Azure
  resources. Never run either without being told to for that specific stack. `pulumi
  preview`, `pulumi stack`, `pulumi config` (without `set`) are the read-only ones.
- Never commit `Pulumi.<stack>.yaml` or any `*.pem` file. Both are gitignored and
  gitleaks runs in CI and in pre-commit.
- Never push directly to `main`, and never overwrite published history.

## Keeping this file current

Propose durable, repo-wide findings (conventions, gotchas, corrected commands) as edits
here, reviewed like any other diff. Personal or environment-specific things go in your
local file instead.

## Local overrides

- Claude Code: `CLAUDE.local.md` at repo root (gitignored). Loads alongside this file.
- Codex: `AGENTS.override.md` at repo root (gitignored). Replaces this file rather than
  adding to it.
- Both are gitignored, so neither exists in a new `git worktree`. To carry personal
  instructions across worktrees, keep them in `~/.claude/<name>.md` and `@`-import that
  from `CLAUDE.local.md`, or in `~/.codex/AGENTS.override.md` for Codex.
