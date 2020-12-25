# Developers

## scripts

`scripts` directory contains convenience scripts for developers.

If you're looking for something that can be considered part of the developer workflow,
check out the `scripts` directory. 

## Virtual environment

This project uses a Python virtual environment.

(Re)create the soda-sql virtual environment with `scripts/recreate_venv.sh`

The virtual environment will be created in directory `{project_root}/.venv`

To activate the virtual environment, run `. .venv/bin/activate` in the project root. 

## Running Tests

The `tests` package contains the different test suites

`python -m pytest tests/local` is the default test suite that must pass before every commit.  It 
runs all the independent tests as well as the tests that are dependent on a local PostgreSQL 
DB.  `tests/postgres_container/docker-compose.yml` can be used to start a local PostgreSQL DB.  You 
can use `scripts/start_test_postgres_db.sh` as a convenience script to launch that container.

`python -m pytest tests/local/independent` runs only the tests that are not dependent 
on anything else except the python interpreter

`python -m pytest tests/warehouses` runs all sql tests on all the warehouses.  Note that to 
run this test suite you have to configure the credentials in `~/.soda/profiles.yml`.  If 
the file does not exist, an initial default version will be created.

## Running Tests with Tox

Tox will start a Postgres database as a docker image and stop it after the tests are finished.

To run all unit tests simply execute the following command:

```
$ tox
```

You may also pass extra parameters. This shows everything written to the standard output (even if tests don't fail):

```
$ tox -- -s
```

This changes the log level:

```
$ tox -- --log-cli-level=DEBUG
```

To generate HTML reports (tests and coverage), execute the following command:

```
$ tox -e html-reports
```

Reports will be available in the directory `./reports/`.