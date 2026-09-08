#!/bin/bash -eu

# Build the Atheris fuzz target for ClusterFuzzLite.
python3 -m pip install --require-hashes -r apps/api/requirements.txt

export PYTHONPATH="$SRC/ai-language-partner/apps/api${PYTHONPATH:+:$PYTHONPATH}"

compile_python_fuzzer .clusterfuzzlite/security_boundaries_fuzzer.py

corpus_dir="$SRC/ai-language-partner/.clusterfuzzlite/corpus/security_boundaries_fuzzer"
if [ -d "$corpus_dir" ]; then
  zip -j "$OUT/security_boundaries_fuzzer_seed_corpus.zip" "$corpus_dir"/*
fi
