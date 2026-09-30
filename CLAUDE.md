# CLAUDE.md

Guidance for working in this repository.

## What this is

`pycharting` — an interactive OHLC charting library for large financial series.
It does not render in Python: it starts a local FastAPI server in a background
thread and draws in the browser, which is what lets it pan and zoom over millions
of points. Runtime dependencies are `fastapi`, `uvicorn[standard]`, `pydantic`,
`pandas` and `numpy`.

The public API is four names, re-exported flat from `pycharting/__init__.py` with
an explicit `__all__`:

```text
plot, stop_server, get_server_status, __version__
```

Under `src/pycharting/`, in the order a call travels:

- `api/interface.py` — the user-facing functions. Bridges numpy/pandas input to
  the server and data layers. `plot()` lives here.
- `data/ingestion.py` — validation and normalisation: equal-length arrays, the
  financial constraints (high ≥ low), and conversion of lists, Series and
  DataFrames into NumPy arrays.
- `core/lifecycle.py` — runs the server on a background thread so the calling
  script or notebook stays responsive, and owns start/stop.
- `core/server.py` — the FastAPI app: serves the static assets and the data
  endpoints.
- `api/routes.py` — the REST endpoints the frontend calls: `/data` (sliced OHLC),
  `/sessions`, `/status`.
- `web/static/` — the frontend. `js/chart.js` draws, `js/viewport.js` handles
  pan/zoom, `js/sync.js` keeps multiple charts aligned; `demo.html`,
  `multi-chart-demo.html` and `viewport-demo.html` are the standalone pages.

`demo.py` at the repo root is the runnable example that produces `demo.png`.

**The frontend is part of the library.** A change to `web/static/js/*.js` ships in
the wheel (`[tool.hatch.build.targets.wheel]`) and is not covered by the Python
test suite — exercise it through the demo pages.

## Ownership: locally owned vs Rhiza-managed

This repo syncs its dev infrastructure from the
[`jebel-quant/rhiza`](https://github.com/jebel-quant/rhiza) template. The pinned
version lives in `.rhiza/template.yml` (`ref:`), currently **`v0.18.8`** — well
behind the current template line, so expect this repo's layout to differ from its
siblings. **The authoritative, machine-generated list of synced files is the
`files:` block of `.rhiza/template.lock`** — when in doubt, consult it.

Only the `github-project` profile is selected, with no `legal` bundle: that is
why there is no `LICENSE`, `SECURITY.md`, `CHANGELOG.md` or `cliff.toml` here.
Adding `legal` to `templates:` in `.rhiza/template.yml` is what would bring them.

### Locally owned — edit these freely

- `src/` — the library source, Python and the shipped `web/static/` frontend
- `tests/` — the test suite
- `pyproject.toml` — project metadata, dependencies, and tool config
- `README.md`, `mkdocs.yml`, `docs/`, `CLAUDE.md`
- `demo.py`, `demo.png`
- `Makefile` — **repo-owned here**, unlike newer rhiza repos. It sets
  `MKDOCS_EXTRA_PACKAGES`, `DEFAULT_AI_MODEL` and `GH_AW_ENGINE`, then
  `include`s `.rhiza/rhiza.mk`. Keep it small; that is what makes it safe to own.
- `.rhiza/template.yml` — the template pin and the `profiles:` selection. The one
  file under `.rhiza/` this repo owns.

### Rhiza-managed — do NOT edit in place; fix upstream

These are overwritten by the next sync. To change one, open a PR against
`jebel-quant/rhiza` (or exclude the path in `.rhiza/template.yml`), then re-sync:

- `.github/workflows/rhiza_*.yml` — all CI/CD workflows
- `.github/` scaffolding — issue/PR/discussion templates, `dependabot.yml`,
  `release.yml`, rulesets, `secret_scanning.yml`
- `.rhiza/rhiza.mk` and the `.rhiza/make.d/*.mk` fragments
- `.pre-commit-config.yaml`, `ruff.toml`, `pytest.ini`, `.bandit`,
  `.editorconfig`, `.python-version`
- `.rhiza/**` other than `template.yml` — completions, assets, `tests/`

## Quality gates

This repo predates rhiza v1.4, so the gates are still the **synced make layer**:
the repo-owned `Makefile` `include`s `.rhiza/rhiza.mk`, which pulls in
`.rhiza/make.d/*.mk`. Run them as bare `make <target>` — never call
`.venv/bin/...` directly. `make help` lists everything, grouped by fragment.

- `make install` — venv and dependencies
- `make fmt` — the pre-commit hooks
- `make typecheck` — `ty`
- `make test` — the suite with the coverage gate
- `make docs-coverage` — interrogate docstring coverage
- `make deptry` — unused/missing dependency analysis
- `make security` — pip-audit and bandit
- `make license` — fail on GPL/LGPL/AGPL
- `make semgrep`, `make suppression-audit`, `make todos` — the quality extras
- `make rhiza-test`, `make test-pyproject` — the template's bundled checks
- `make doctor` — verify local prerequisites
- `make benchmark`, `make hypothesis-test`, `make stress` — the test extras
- `make book` / `make serve` — build the companion book, and serve it on :8000
- `make all` — `fmt deptry test docs-coverage security license typecheck rhiza-test`

**`make mutation` still exists in this repo's make layer — do not use it.** rhiza
v1.5.0 stopped offering mutation testing (Jebel-Quant/rhiza#1492); the recipe
drives a mutmut 2.x CLI that mutmut 3 removed, so it is broken rather than merely
deprecated. It will disappear when this repo's template pin moves forward.

## Conventions

- The coverage gate is `COVERAGE_FAIL_UNDER`, default **90** in
  `.rhiza/make.d/test.mk`. This repo does not raise it.
- Every public symbol needs a docstring. The module docstrings here are unusually
  substantial — `api/interface.py` carries the usage example — and
  `make docs-coverage` keeps them present. Keep the `plot()` example in
  `__init__.py` runnable.
- Dependency bounds are upper-capped on purpose (`fastapi<1.0.0`,
  `pandas<3.0.0`, `numpy<3.0.0`, `pydantic<3.0.0`, `uvicorn<1.0.0`). Raising one
  is a compatibility decision, not routine maintenance.
- Validation belongs in `data/ingestion.py` and runs before anything reaches the
  server. Do not scatter shape or ordering checks into the route handlers.
- The server runs on a background thread (`core/lifecycle.py`). Anything holding
  state across requests has to be safe against that; prefer passing data through
  the session mechanism in `api/routes.py` over module-level globals.
- Three markers are declared: `stress`, `property`, `kaleido`.
- The per-test timeout is 60s (`pytest-timeout`). A browser-driven test that
  needs longer belongs behind the `stress` marker.

## Test layout

Tests mirror the source one file per module, under a `tests/pycharting/` root that
repeats the package name:

```text
src/pycharting/api/interface.py   → tests/pycharting/api/test_interface.py
src/pycharting/api/routes.py      → tests/pycharting/api/test_routes.py
src/pycharting/core/lifecycle.py  → tests/pycharting/core/test_lifecycle.py
src/pycharting/core/server.py     → tests/pycharting/core/test_server.py
src/pycharting/data/ingestion.py  → tests/pycharting/data/test_ingestion.py
```

Shared fixtures live in `tests/pycharting/conftest.py`. Every directory carries an
`__init__.py`, so keep adding them — the layout is package-based, not
rootdir-relative.

There is no coverage of `web/static/js/*.js`, by construction. A frontend change
needs manual verification through `demo.py` or the `*-demo.html` pages; the Python
gates will pass regardless.
