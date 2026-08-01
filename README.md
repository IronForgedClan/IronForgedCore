<h1 align="center">Iron Forged Core</h1>
<p align="center">
<img alt="Version" src="https://img.shields.io/github/v/release/IronForgedClan/IronForgedCore?include_prereleases&label=core">
<a href="https://github.com/IronForgedClan/IronForgedCore/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/IronForgedClan/IronForgedCore"></a>
<a href="https://github.com/psf/black"><img alt="Code style: Black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

A Python library for the Iron Forged Old School RuneScape clan. Database models,
business logic, migrations, and helpers used by the bot and the API projects.

## What is ironforgedcore

`ironforgedcore` is a Python library. You install it from a git tag into a
consumer project, and that consumer reads the same database and runs the same
business logic.

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

## Installation

Pin a specific tag in your `requirements.in` or `pyproject.toml`:

```
ironforgedcore @ git+https://github.com/ironforgedclan/ironforgedcore.git@v0.1.0
```

## Local Development

The core uses [uv](https://docs.astral.sh/uv/) as its package manager.
Install uv on your host:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone and install:

```sh
git clone https://github.com/IronForgedClan/IronForgedCore.git
cd IronForgedCore
uv sync
```

## Migrations

Schema changes live under `ironforgedcore/alembic/versions/`. The Alembic config
is at `ironforgedcore/alembic.ini`.

Apply migrations:

```sh
make migrate
```

Create a new migration:

```sh
make revision DESC="description of the change"
```

This generates a new file under `ironforgedcore/alembic/versions/`. Edit the
file to add your column or table logic.

Revert a migration:

```sh
make downgrade
```

## Makefile

| Target                     | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `make test`                | Install dev dependencies and run the full test suite.                    |
| `make format`              | Format the codebase using Black.                                         |
| `make migrate`             | Apply all pending database migrations.                                   |
| `make revision DESC="..."` | Create a new Alembic migration. The `DESC` becomes part of the filename. |
| `make downgrade`           | Revert the most recent migration.                                        |
| `make build-prod`          | Build a wheel and sdist into `dist/`.                                    |
| `make rmi-prod`            | Remove `dist/`, `build/`, and `*.egg-info`.                              |
| `make clean`               | Remove build artifacts and `__pycache__` directories.                    |

## Testing

All test files live in `tests/`. The structure mirrors the package:
`ironforgedcore/services/ingot_service.py` is tested by
`tests/services/ingot_service_test.py`.

```sh
make test
```

## Contributing

Contributions must:

- Address a specific issue by ticket number.
- Pass all tests in the test suite.
- Conform to the Black formatter.
- Include tests for any new functionality.

This codebase uses the [Black](https://github.com/psf/black) formatter, enforced
through a workflow that runs on all pull requests into `main`.
