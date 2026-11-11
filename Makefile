.DEFAULT_GOAL := build

# Examples: make build ID=1070; make test ID=1070; make add ID=1071 USERNAME=you
JOBS ?= 2
PYTHON ?= python3
# Some shells export the OS login as USERNAME; do not mistake it for a CSES account.
ifeq ($(origin USERNAME),environment)
USERNAME :=
endif
PROBLEMS := $(sort $(patsubst problems/%/main.cpp,%,$(wildcard problems/[0-9]*/main.cpp)))

.PHONY: help init configure build test test-all check run open submit add download-tests list clean distclean check-id

help:
	@printf '%s\n' \
	  'make init                  Restore missing tests and configure after cloning' \
	  'make                       Build all problems' \
	  'make build ID=1070         Build one problem' \
	  'make test ID=1070          Build and test one problem' \
	  'make test ID=1070 CASE=3    Run one test (or CASE=1,3,7)' \
	  'make test-all              Build and test every problem' \
	  'make check                 Run offline tooling regression tests' \
	  'make run ID=1070           Build and run (stdin supported)' \
	  'make run ID=1070 CASE=2,3,5-9  Run selected input files (builds once)' \
	  'make open ID=1069          Open main.cpp (override with OPEN_WITH=vim)' \
	  'make submit ID=1070        Test and submit to CSES (confirmation required)' \
	  'make add ID=1070           Add a problem; uses .env or prompts' \
	  'make download-tests ID=1070  Restore tests; uses .env or prompts' \
	  'make list                  List problem IDs' \
	  'make clean                 Remove compiled outputs' \
	  'make distclean             Remove the entire build directory' \
	  'Options: JOBS=4, PYTHON=python3'

init:
	$(PYTHON) scripts/init.py $(if $(USERNAME),"$(USERNAME)")

check:
	$(PYTHON) -m unittest discover -s tests -t . -p 'test_*.py' -v

# Configure a fresh build once; CMake's build system tracks later CMake changes.
build/CMakeCache.txt:
	cmake -S . -B build

# Explicitly requesting configure still forces a configuration pass.
configure:
	cmake -S . -B build

check-id:
	@case "$(ID)" in ''|*[!0-9]*) echo 'Provide a numeric problem ID: ID=1070' >&2; exit 1;; esac

build: build/CMakeCache.txt
	$(if $(ID),$(MAKE) --no-print-directory check-id, @:)
	cmake --build build --parallel $(JOBS) $(if $(ID),--target problem_$(ID))

test: check-id build/CMakeCache.txt
	cmake -E env "CSES_TEST_CASES=$(CASE)" cmake --build build --target test_$(ID) --parallel $(JOBS)

test-all: build/CMakeCache.txt
	@set -e; for id in $(PROBLEMS); do \
	  cmake --build build --target test_$$id --parallel $(JOBS); \
	done

run: check-id
	@$(PYTHON) scripts/run_problem.py "$(ID)" "$(CASE)"

open: check-id
	$(PYTHON) scripts/open_problem.py "$(ID)" $(if $(OPEN_WITH),--editor "$(OPEN_WITH)")

submit: check-id
	$(PYTHON) scripts/submit.py "$(ID)" $(if $(USERNAME),"$(USERNAME)")

add: check-id
	$(PYTHON) scripts/add_problem.py "$(ID)" $(if $(USERNAME),"$(USERNAME)")

download-tests: check-id
	$(PYTHON) scripts/add_problem.py "$(ID)" $(if $(USERNAME),"$(USERNAME)") --tests-only

list:
	@printf '%s\n' $(PROBLEMS)

clean:
	@if [ -f build/CMakeCache.txt ]; then cmake --build build --target clean; fi
	@find build -type f -name 'actual_*.txt' -delete 2>/dev/null || true

distclean:
	cmake -E rm -rf build
