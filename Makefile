.PHONY: check build

check:
	python3 tools/build_codex.py --check
	python3 tools/check_english.py
	python3 -m unittest discover -s tests

build:
	python3 tools/build_codex.py
