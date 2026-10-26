# CI/CD-specific coverage upload integration

Per-CI-system upload blocks for Codacy coverage reporting. Add a coverage upload step to the CI/CD pipeline **after** the test/coverage step.

## GitHub Actions

```yaml
- name: Upload coverage to Codacy
  env:
    CODACY_PROJECT_TOKEN: ${{ secrets.CODACY_PROJECT_TOKEN }}
  run: bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r <report-file>
```

Or use the official action:

```yaml
- name: Upload coverage to Codacy
  uses: codacy/codacy-coverage-reporter-action@v1
  with:
    project-token: ${{ secrets.CODACY_PROJECT_TOKEN }}
    coverage-reports: <report-file>
```

## GitLab CI

```yaml
upload-coverage:
  stage: test
  script:
    - bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r <report-file>
  variables:
    CODACY_PROJECT_TOKEN: $CODACY_PROJECT_TOKEN
```

## CircleCI (using orb)

```yaml
orbs:
  codacy: codacy/coverage-reporter@13
workflows:
  main:
    jobs:
      - test
      - codacy/upload_coverage:
          requires: [test]
```

## Travis CI

```yaml
after_success:
  - bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r <report-file>
```

## Bitbucket Pipelines

```yaml
- step:
    name: Upload coverage
    script:
      - bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r <report-file>
```

## Alpine Linux (no bash)

```bash
wget -qO - https://coverage.codacy.com/get.sh | sh -s -- report -r <report-file>
```

See also [references/coverage-upload.md](coverage-upload.md) for advanced upload scenarios.
