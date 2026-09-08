# Security boundary fuzzing

This directory contains the ClusterFuzzLite integration for the URL and filesystem containment helpers covered by issue #105.

## Local smoke run

Install the backend dependencies and Atheris in a Python 3.11 environment, then run:

```bash
python .clusterfuzzlite/security_boundaries_fuzzer.py -runs=1000
```

The target accepts three input modes: `u` for AnkiConnect URLs, `s` for safe path segments, and `p` for contained filesystem paths. The checked-in seed corpus is under `.clusterfuzzlite/corpus/security_boundaries_fuzzer/`.

The harness never performs network access. Filesystem cases use a temporary fixture tree and assert that successful resolutions remain inside the fixture root.
