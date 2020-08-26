# circleci-validation-pre-commit

[pre-commit](https://pre-commit.com/) hook for validating circleci config. It
uses [CircleCI CLI](https://github.com/CircleCI-Public/circleci-cli.) to perform
validation of CircleCI config.

**Note**: The validation seems to be slow so it may be a good option to run it
as a pre-push hook. It will be extra slow on the first run as it has to download
and extract the CLI binary.

## Usage
Example `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/AleksaC/circleci-validation-pre-commit
    rev: master
    hooks:
      - id: circle-ci-validator
```

## Contact 🙋‍♂️
- [Personal website](https://aleksac.me)
- <a target="_blank" href="http://twitter.com/aleksa_c_"><img alt='Twitter followers' src="https://img.shields.io/twitter/follow/aleksa_c_.svg?style=social"></a>
- aleksacukovic1@gmail.com
