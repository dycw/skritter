# python-project-template

Python project template that I use. I use:

- [conda](https://docs.conda.io/en/latest/) to manage my environments,
- [mypy](https://github.com/python/mypy) to statically type-check my code,
- [pytest](https://docs.pytest.org/en/stable/) to test my code,
  - [pytest-randomly](https://github.com/pytest-dev/pytest-randomly) for test-order randomization,
  - [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) for loop-on-fail monitoring and distributed testing,
- [pre-commit](https://pre-commit.com/) to format, lint and `mypy` my code,
  - [add-trailing-comma](https://github.com/asottile/add-trailing-comma), [black](https://github.com/psf/black) and [pyupgrade](https://github.com/asottile/pyupgrade) to format my code,
  - [autoflake](https://github.com/myint/autoflake) to remove unneeded imports,
  - [reorder-python-imports](https://github.com/asottile/reorder_python_imports) to reorder imports,
  - [flake8](https://github.com/PyCQA/flake8) to lint my code,
  - [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) to perform generic linting,
  - [nitpick](https://github.com/andreoliwa/nitpick) to ensure settings' consistency across projects,
- [bump2version](https://github.com/c4urself/bump2version) to version bump my code,
- [Github workflows](https://docs.github.com/en/actions/configuring-and-managing-workflows) to run my CI,
  - [automerge](https://github.com/pascalgn/automerge-action) to merge passing PRs,
  - [action-autotag](https://github.com/ButlerLogic/action-autotag) to tag releases,
- [PyCharm](https://www.jetbrains.com/pycharm/) to write my code.
