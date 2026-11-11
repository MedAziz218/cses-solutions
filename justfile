# Run `just` to build everything, or `just help` for shortcuts.
default:
    @make --no-print-directory

help:
    @just --list

# Restore missing tests and configure after cloning; credentials prompted if needed
init username="":
    @make --no-print-directory init USERNAME="{{username}}"

# Restore tests for one existing problem without changing its solution
download-tests id username="":
    @make --no-print-directory download-tests ID="{{id}}" USERNAME="{{username}}"

# Build all problems, or one: just build 1070
build id="":
    @make --no-print-directory build ID="{{id}}"

# Test all cases, or select cases: just test 1068 3 / just test 1068 1,3,7
test id cases="":
    @make --no-print-directory test ID="{{id}}" CASE="{{cases}}"

# Build and test every problem (unsolved starters will fail)
test-all:
    @make --no-print-directory test-all

# Run with stdin or input selections: just run 1069 / just run 1069 2,3,5-9
run id case="":
    @make --no-print-directory run ID="{{id}}" CASE="{{case}}"

# Open main.cpp; override the editor with: just open 1069 vim
open id editor="":
    @make --no-print-directory open ID="{{id}}" OPEN_WITH="{{editor}}"

# Run all local tests, then submit to CSES only after default-no confirmation
submit id username="":
    @make --no-print-directory submit ID="{{id}}" USERNAME="{{username}}"

# Download tests and create an empty starter; uses .env or prompts
add id username="":
    @make --no-print-directory add ID="{{id}}" USERNAME="{{username}}"

# Run offline tooling tests (not problem solution tests)
check:
    @make --no-print-directory check

# Configure CMake without building
configure:
    @make --no-print-directory configure

# List available problem IDs
list:
    @make --no-print-directory list

# Remove compiled outputs, keeping CMake configuration
clean:
    @make --no-print-directory clean

# Remove the entire build directory
distclean:
    @make --no-print-directory distclean
