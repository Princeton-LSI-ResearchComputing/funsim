# Contributing to the NeuroSimulator project

This document described the basics of how to set up the NeuroSimulator Project repository
in order to start developing/contributing.

## Getting Started

### Install Python Dependencies

#### Python

Install the latest Python (version 3.9.1), and make sure it is in your path:

    $ python --version
    Python 3.9.1

Test to make sure that the `python` command now shows your latest python install:

    $ python --version
    Python 3.9.1


### Setup the NeuroSimulator project

#### Clone the repository

    git clone https://github.com/Princeton-LSI-ResearchComputing/neuron-simulator.git
    cd neuron-simulator

#### Create a virtual environment

Create a virtual environment (from a bash shell) and activate it, for example:

    python3 -m venv .venv
    source .venv/bin/activate

Install Django and dependencies as well as linters and other
development related tools. Use `requirements/prod.txt` for production
dependencies.

    python -m pip install -U pip  # Upgrade pip
    python -m pip install -r requirements/dev.txt  # Install requirements

#### Verify Installations

Django:

    python
    > import django
    > print(django.get_version())
    3.2.4

### Configure NeuroSimulator

Create a new secret:

    python -c "import secrets; print(secrets.token_urlsafe())"

Database and secret key information should not be stored directly in settings
that are published to the repository.  We use environment variables to store
configuration data.  This makes it possible to easily change between
environments of a deployed application (see [The Twelve-Factor
App](https://www.12factor.net/config)).  The .env file you create here is pre-
configured to be ignored by the repository, so do not explicitly check it in.

Copy the NeuroSimulator environment example:

    cp config/.env.example config/.env

Update the .env file to reflect the new secret key (append the key to "SECRET_KEY=")

SQlite is used for this project, so no database credentials are needed for configuration.

### Start NeuroSimulator

Set up the project's SQLite database:

    python manage.py migrate

Note: a file named "neurodb.sqlite3" should be created.

Verify you can run the development server.  Run:

    python manage.py runserver

Then go to this site in your web browser:

    http://127.0.0.1:8000/

## Pull Requests

### Code Formatting Standards

All pull requests must pass linting prior to being merged.

Currently, all pushes are linted using [GitHub's
Super-Linter](https://github.com/github/super-linter). The configuration files
for the most used linters have been setup in the project root to facilitate
linting on developers machines. These include:

* [Markdown-lint](https://github.com/igorshubovych/markdownlint-cli#readme) - `.markdown-lint.yml`
* [Flake8](https://flake8.pycqa.org/en/latest/) - `.flake8`
* [Pylint](https://www.pylint.org/) - `.python-lint` -> `.pylintrc`
* [isort](https://pycqa.github.io/isort/) - `.isort.cfg`

#### Linting

Linting for this project runs automatically on GitHub when a PR is submitted,
but this section describes how to lint your changes locally.

##### Individual linters

For the most commonly used linters (*e.g.* for python, HTML, and Markdown
files) it is recommended to install linters locally and run them in your
editor. Some linters that may be useful to install locally include:

* Python
  * [Flake8](https://flake8.pycqa.org/en/latest/) - python style checker
  * [Pylint](https://www.pylint.org/) - python code analysis
  * [Black](https://black.readthedocs.io/en/stable/) - code formatter
  * [isort](https://pycqa.github.io/isort/) - sort imports
  * [mypy](https://mypy.readthedocs.io/) - static type checker
* HTML
  * [HTMLHint](https://htmlhint.com/) - static analysis for HTML
* Markdown
  * [Markdown-lint](https://github.com/igorshubovych/markdownlint-cli#readme)
    \- style checker for Markdown
* General
  * [jscpd](https://github.com/kucherenko/jscpd) - Copy/paste detector for
    programming source code

It is recommended to run superlinter (described below) routinely or
automatically before submitting a PR, but if you want a quick check while
developing, you can run these example linting commands on the command line:

    black .
    isort .
    markdownlint .
    flake8 .
    pylint NeuroSimulator FuncAtlas *.py
    dotenv-linter NeuroSimulator FuncAtlas

##### Superlinter

In addition to linting files as you write them, developers may wish to [run
Superlinter on the entire repository
locally](https://github.com/github/super-linter/blob/master/docs/run-linter-locally.md).
This is most easily accomplished using [Docker](https://docs.docker.com/get-docker/)].
Create a script outside of the repository that runs superlinter via docker and run it
from the repository root directory. Example script:

    #!/usr/bin/env sh
    docker pull github/super-linter:latest

    docker run \
        -e FILTER_REGEX_EXCLUDE="(\.pylintrc|migrations|static\/bootstrap.*)" \
        -e LINTER_RULES_PATH="/" \
        -e IGNORE_GITIGNORED_FILES=true \
        -e RUN_LOCAL=true \
        -v /full/path/to/neuron-simulator/:/tmp/lint github/super-linter

Note: The options `FILTER_REGEX_EXCLUDE`, `LINTER_RULES_PATH`, and
`IGNORE_GITIGNORED_FILES` should match the settings in the GitHub Action in
`.github/workflows/superlinter.yml`

### Testing

#### Test Implementation

All pull requests must implement tests of the changes implemented prior to being
merged.  Each app should either contain `tests.py` or a `tests` directory
containing multiple test scripts.  Currently, all tests are implemented using
the TestCase framework.

See these resources for help implementing tests:

* [Testing in Django (Part 1) - Best Practices and
  Examples](https://realpython.com/testing-in-django-part-1-best-practices-and-examples/)
* [Django Tutorial Part 10: Testing a Django web
  application](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Testing)

All pull requests must pass all previous and new tests:

    python3 manage.py test

#### Quality Control

All pull requests must pass new and all previous tests before merging.  Run the
following locally before submitting a pull request:

    python manage.py test

### Model Updates

Any pull requests that include changes to the model, must include an update to
the migrations and the resulting auto-generated migration scripts must be
checked in.

#### Migration Process

Create the migration scripts:

    python manage.py makemigrations

Check for unapplied migrations:

    python manage.py showmigrations

Apply migrations to the database:

    python manage.py migrate
