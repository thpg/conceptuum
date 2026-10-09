# Local setup and troubleshooting

This guide supplements the [README](../README.md). Code version:
[0.1.0-dev](../VERSION). Data revision: **2026-10-09 / Q9**.

## Prerequisites

Install Python 3.9 or newer, a running MariaDB server, and a MariaDB client
available as `mariadb` or `mysql`. Install Go 1.26.1 or newer only to run the
visualizer. `requirements.txt` pins PyMySQL 1.2.0 and pymorphy3 2.0.6.
The latter supports Russian morphological matching; the engine can also run
with PyMySQL alone, with reduced matching when morphology is unavailable.

The local setup was checked with Python 3.9.13, Go 1.26.1, and MariaDB 5.5.42.
The live Q9 import and visualizer were also checked on MariaDB 11.8.6 during
the [Q9 deployment](quality/2026-10-09-q9.md). Other database
versions and MySQL remain unverified. For upstream requirements, see [PyMySQL](https://pypi.org/project/PyMySQL/),
[pymorphy3](https://pypi.org/project/pymorphy3/), and
[Go toolchain selection](https://go.dev/doc/toolchain).

## Database import

Run the client from the repository root and use its `SOURCE` command as shown
in the README. The dump contains `CREATE DATABASE`, `USE jnana3`, and
`DROP TABLE IF EXISTS` statements. It replaces the six project tables.
The importer needs privileges for those statements. Supplying another
database as a client argument does not override the dump's `USE` statement.

The snapshot's tables use the legacy `utf8` character set. A client setting
of `utf8mb4` does not migrate the tables to a different character set.

For a command reference, see the
[MariaDB client documentation](https://mariadb.com/docs/server/clients-and-utilities/mariadb-client/mariadb-command-line-client).

## Python connection settings

Set these variables **before starting Python**:

| Variable | Meaning | Example |
|---|---|---|
| `JNANA_HOST` | Server hostname/IP | `127.0.0.1` |
| `JNANA_PORT` | Integer TCP port, 1–65535 | `3306` |
| `JNANA_DATABASE` | Imported database | `jnana3` |
| `JNANA_USER` | Your database account | `conceptuum` |
| `JNANA_PASSWORD` | That account's password; an empty value is allowed | Set locally |

These configure `ask.py`, the Python engine, audits, and the reviewed batch
runner. They do not create a database account. Existing local defaults remain
as a compatibility fallback; configure your own account explicitly.

For Python applications, constructor arguments override these defaults:

```python
eng = JnanaEngine(database="a_separate_test_database", user="your_account")
```

Environment values are read when `jnana_engine` is imported. Restart a running
Python process after changing them. A `.env` file is not loaded automatically.
`JNANA_DSN` is a Go driver DSN and is not used by Python.

Reading the snapshot through the engine, retrieval demo, visualizer, and
auditors needs `SELECT` access to the six tables. Maintenance commands need
additional write privileges. Use an account with privileges appropriate to
the command you are running.

## Visualizer settings

| Variable | Meaning |
|---|---|
| `JNANA_DSN` | Go MySQL driver connection string, including user, password, host, port, and database |
| `LISTEN` | Bind address; default `127.0.0.1:7100` |

Start `go run .` with `visualizer/` as the current directory. HTML, CSS, JavaScript,
and version metadata are read from `static/` at runtime, including when using a
built binary. Deploy the entire directory alongside the executable. The server
exposes `/`, `/static/`, `/api/search`, `/api/concept`, `/api/tree`, and `/api/euler`.
See the [visualizer guide](../visualizer/README.md) for controls and browser checks.

## Common problems

| Symptom | Check |
|---|---|
| `No module named pymysql` | Install `requirements.txt` with the same Python interpreter that runs the command |
| PowerShell cannot run `Activate.ps1` | Use `.\.venv\Scripts\python.exe` directly instead of activating |
| `mariadb` is not recognized | Add the client to `PATH`, use its installed full path, or use `mysql` if that is its name |
| Connection refused | Start the server and check the configured host and port |
| Access denied | Check the database account, password, and allowed client host |
| Unknown database / missing table | Import the snapshot and point the client at `jnana3` |
| Python works but the visualizer cannot connect | Set `JNANA_DSN`; the Go application does not read Python's separate variables |
| The visualizer returns 404 for `/` | Run it from `visualizer/` so `static/index.html` can be found |
| English retrieval prints Russian definitions | `--lang` affects lookup; cached definitions retain their stored language |
| Encoding error when piping output on Windows | Set `$env:PYTHONIOENCODING = 'utf-8'` before running Python |
| LLM endpoint is unreachable | Use `--no-llm`, or start a compatible server and supply its URL and loaded model name |

The CLI client import, Python retrieval, and visualizer are separate steps.
Starting the visualizer does not install Python packages or import the database.
