# circleci-cli-py

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Test Status](https://dev.azure.com/aleksac/aleksa-oss/_apis/build/status/AleksaC.circleci-cli-py?branchName=master)](https://dev.azure.com/aleksac/aleksa-oss/_build?definitionId=11&_a=summary)
[![Autoupdater Status](https://circleci.com/gh/AleksaC/circleci-cli-py.svg?style=svg)](https://circleci.com/gh/AleksaC/circleci-cli-py)

A python package that provides a pip-installable
[CircleCI CLI](https://github.com/CircleCI-Public/circleci-cli) binary.

The mechanism by which the binary is downloaded is basically copied from
[shellcheck-py](https://github.com/shellcheck-py/shellcheck-py).

## Getting started

### Installation

The package hasn't been published to PyPI yet, and may never be, as its primary
purpose doesn't require it. However you can install it through git:

```shell script
pip install git+git://github.com/AleksaC/circleci-cli-py.git@v0.1.24435
```

### With pre-commit

This package was primarily built to provide a convenient way of running hadolint
as a [pre-commit](https://pre-commit.com) hook, since pre-commit seems unable to
install it as a golang hook.

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/AleksaC/circleci-cli-py
    rev: v0.1.24435
    hooks:
      - id: circle-ci-validator
```

## Contact 🙋‍♂️
- [Personal website](https://aleksac.me)
- <a target="_blank" href="http://twitter.com/aleksa_c_"><img alt='Twitter followers' src="https://img.shields.io/twitter/follow/aleksa_c_.svg?style=social"></a>
- aleksacukovic1@gmail.com
