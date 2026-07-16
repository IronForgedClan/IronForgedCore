<h1 align="center">Iron Forged Core</h1>
<p align="center">
<img alt="Version" src="https://img.shields.io/github/v/release/IronForgedClan/IronForgedCore?include_prereleases&label=core">
<a href="https://github.com/IronForgedClan/IronForgedCore/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/IronForgedClan/IronForgedCore"></a>
<a href="https://github.com/psf/black"><img alt="Code style: Black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<p align="center">A shared Python library for the Iron Forged Old School RuneScape clan. Database models, business logic, migrations, and helpers used by the bot and the API.</p>

## What is ironforgedcore

`ironforgedcore` is a Python library. It is not a runnable service. There is no
`main.py` and no Docker image. You install it from a git tag into a consumer
project, and that consumer reads the same database and runs the same business
logic.

The package contains:

- Database engine and session factory (`ironforgedcore.database`)
- ORM models for members, scores, changelogs, raffles, API consumers, and audit
  logs (`ironforgedcore.models`)
- Business-logic services: ingots, raffles, member lookups, score history, WOM
  integration (`ironforgedcore.services`)
- Pure enums and helpers: ranks, roles, activity checks, WOM to Discord role
  mapping, text formatters (`ironforgedcore.common`)
- Alembic migrations under `ironforgedcore/alembic/versions/`
- HTTP client, retry decorator, in-memory caches, event emitter, structured
  logger

For usage examples, see the consumer projects:

- [IronForgedBot](https://github.com/IronForgedClan/IronForgedBot) - the Discord
  bot
- [IronForgedApi](https://github.com/IronForgedClan/IronForgedApi) - the REST
  API

## Installation (downstream consumers)

Pin a specific tag in your consumer's `requirements.in` or `pyproject.toml`:

```
ironforgedcore @ git+https://github.com/ironforgedclan/ironforgedcore.git@v0.1.0
```

Then regenerate your lockfile (`make update-deps` or `pip-compile`) and install.
No auth tokens are required. The repository is public.

When a new core version ships, bump the `@vX.Y.Z` pin in each consumer and
rebuild.

## Local Development

### Clone the repository

```sh
git clone https://github.com/IronForgedClan/IronForgedCore.git
cd IronForgedCore
```

### Set up a virtual environment

It is recommended to use Python's virtual environments.

```sh
python -m venv .venv
source .venv/bin/activate
```

### Install with dev dependencies

```sh
pip install -e .[dev]
```

This installs the package in editable mode plus the test and lint tools.

## Migrations

Schema changes live under `ironforgedcore/alembic/versions/`. The Alembic config
is at `ironforgedcore/alembic.ini`.

### Apply migrations to your database

```sh
make migrate
```

This runs `alembic upgrade head` against the database URL in your environment.

### Create a new migration

```sh
make revision DESC="short description of the change"
```

This generates a new file under `ironforgedcore/alembic/versions/`. Edit the
file to add your column or table logic.

> [!NOTE]
> Both consumer projects run `alembic upgrade head` on startup. A new migration
> only needs to ship once.

### Revert a migration

```sh
make downgrade
```

This runs `alembic downgrade -1`.

## Makefile

A small set of targets, since this is a library:

- `make test`\
  Installs dev dependencies and runs the full test suite.

- `make format`\
  Formats the codebase using Black.

- `make migrate`\
  Applies all pending database migrations.

- `make revision DESC="..."`\
  Creates a new Alembic migration. The `DESC` becomes part of the filename.

- `make downgrade`\
  Reverts the most recent migration.

- `make build-prod`\
  Builds a wheel and sdist into `dist/` (for backup or one-off installs).

- `make rmi-prod`\
  Removes `dist/`, `build/`, and `*.egg-info`.

- `make clean`\
  Removes build artifacts and `__pycache__` directories.

> If a `make` command doesn't work, open the `Makefile` to view the underlying
> command and run that instead.

## Versioning

Semver `vX.Y.Z`. Bump `version` in `ironforgedcore/pyproject.toml` and tag the
commit. The wheel and sdist are attached to the GitHub release as a fallback.
There is no package registry. Consumers install via the git URL, see
[Installation](#installation-downstream-consumers).

## Testing

All test files live in `tests/`. The structure mirrors the package:
`ironforgedcore/services/ingot_service.py` is tested by
`tests/services/ingot_service_test.py`.

To run the full suite:

```sh
make test
```

This invokes `python run_tests.py`, which uses `unittest` discovery with the
`*_test.py` pattern. To run a single file or test method directly, use
`python -m unittest`.

When creating new test files, the filename must follow the pattern `*_test.py`
and the class name must follow the pattern `Test*`. Async tests use
`unittest.IsolatedAsyncioTestCase`.

## Data Files

`data/` ships with the repository and contains four JSON files that the storage
layer loads at import time:

- `skills.json` - OSRS skills with XP-per-point values
- `bosses.json` - boss encounters with KC-per-point values
- `clues.json` - clue scroll tiers with KC-per-point values
- `raids.json` - raid activities with KC-per-point values

In this repository the files are stubs sufficient for the test suite. In the
consumer projects, `data/` is a git submodule that overrides the stubs with the
live data.

## Contributing

Contributions must:

- Address a specific issue by ticket number.
- Pass all tests in the test suite.
- Code style must conform to the Black formatter.
- If the contribution adds new functionality, tests covering this must also be
  added.

### Formatting

This codebase uses the [Black](https://github.com/psf/black) formatter.
Extensions are available for many
[popular editors](https://black.readthedocs.io/en/stable/integrations/editors.html).
This is enforced through a workflow that runs on all pull requests into `main`.

> By using Black, you agree to cede control over minutiae of hand-formatting. In
> return, Black gives you speed, determinism, and freedom from pycodestyle
> nagging. You will save time and mental energy for more important matters.
