# Tests

Run everything from the repository root. Each test is a plain Python script, not a pytest suite: it prints what it
checks and exits non-zero if anything failed. These are the commands the Test workflow runs:

```sh
python3 tests/test_integration.py 30
python3 tests/test_release.py
```

| Script | What it checks |
|---|---|
| `test_integration.py` | Integration tests: the real integration code against a fake TrueNAS on a virtual clock |
| `test_release.py` | The release scripts in `scripts/`: the version check and notes, building and checking the zip, publishing to a fake Gitea server, and working out which releases GitHub still needs |

[CONTRIBUTING.md](../CONTRIBUTING.md#checking-a-change) says which to run for which change, and how long each takes.
The tests stand in for Home Assistant (`stubs/`), so they can't prove the integration works on a real Home
Assistant: try changes on a real installation too.
