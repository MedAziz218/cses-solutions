cmake_minimum_required(VERSION 3.16)

# Shared test runner script
# Usage: cmake -D PROG=<path_to_binary> -D TEST_DIR=<path_to_test_dir> -D BINARY_DIR=<path_to_binary_dir> -P cmake/test_runner.cmake

# Optional: -DTEST_CASES=1,3,7 or the CSES_TEST_CASES environment variable.
if(NOT DEFINED TEST_CASES)
    set(TEST_CASES "$ENV{CSES_TEST_CASES}")
endif()

if(NOT "${TEST_CASES}" STREQUAL "")
    string(REPLACE "," ";" SELECTED_CASES "${TEST_CASES}")
    set(TEST_INPUTS "")
    foreach(CASE IN LISTS SELECTED_CASES)
        string(STRIP "${CASE}" CASE)
        if(NOT CASE MATCHES "^[0-9]+(\\.txt)?$")
            message(FATAL_ERROR "Invalid test case '${CASE}'; use names like 1 or 01, separated by commas.")
        endif()
        string(REGEX REPLACE "\\.txt$" "" CASE "${CASE}")
        set(INPUT "${TEST_DIR}/in/${CASE}.txt")
        if(NOT EXISTS "${INPUT}")
            message(FATAL_ERROR "Test case not found: ${INPUT}")
        endif()
        list(APPEND TEST_INPUTS "${INPUT}")
    endforeach()
    list(REMOVE_DUPLICATES TEST_INPUTS)
else()
    file(GLOB TEST_INPUTS "${TEST_DIR}/in/*.txt")
    list(SORT TEST_INPUTS)
endif()

set(TOTAL_TESTS 0)
set(PASSED 0)
set(FAILED 0)

foreach(idx IN LISTS TEST_INPUTS)
    math(EXPR TOTAL_TESTS "${TOTAL_TESTS} + 1")
endforeach()

if(TOTAL_TESTS EQUAL 0)
    message(FATAL_ERROR "No test inputs found in ${TEST_DIR}/in/. Run make init or just init to download them.")
endif()

foreach(idx IN LISTS TEST_INPUTS)
    get_filename_component(BASENAME "${idx}" NAME)       # e.g. "01.txt"
    string(REGEX REPLACE "(\\.txt)$" ".out" EXPECTED_NAME "${BASENAME}")
    set(OUTPUT "${BINARY_DIR}/actual_${BASENAME}")
    set(EXPECTED "${TEST_DIR}/out/${EXPECTED_NAME}")

    execute_process(
        COMMAND "${PROG}"
        INPUT_FILE "${idx}"
        TIMEOUT 10
        OUTPUT_FILE "${OUTPUT}"
        ERROR_VARIABLE ERR
        RESULT_VARIABLE RES
    )

    if(RES STREQUAL "0" AND EXISTS "${EXPECTED}")
        file(READ "${EXPECTED}" EXPECTED_CONTENT)
        file(READ "${OUTPUT}" ACTUAL_CONTENT)

        string(REGEX REPLACE "[ \t\r\n]+" " " EXPECTED_CONTENT "${EXPECTED_CONTENT}")
        string(REGEX REPLACE "[ \t\r\n]+" " " ACTUAL_CONTENT "${ACTUAL_CONTENT}")
        string(STRIP "${EXPECTED_CONTENT}" EXPECTED_CONTENT)
        string(STRIP "${ACTUAL_CONTENT}" ACTUAL_CONTENT)

        if(EXPECTED_CONTENT STREQUAL ACTUAL_CONTENT)
            message(STATUS "  pass: ${BASENAME}")
            math(EXPR PASSED "${PASSED} + 1")
        else()
            message(SEND_ERROR "  FAIL: ${BASENAME}")
            message(STATUS "  Expected:\n${EXPECTED_CONTENT}")
            message(STATUS "  Actual:\n${ACTUAL_CONTENT}")
            math(EXPR FAILED "${FAILED} + 1")
        endif()
    else()
        if(NOT EXISTS "${EXPECTED}")
            message(WARNING "  skip: ${BASENAME} (no expected output)")
            math(EXPR FAILED "${FAILED} + 1")
        else()
            message(SEND_ERROR "  crash: ${BASENAME} (exit code ${RES})")
            if(RES GREATER 0)
                message(STATUS "  stderr: ${ERR}")
            endif()
            math(EXPR FAILED "${FAILED} + 1")
        endif()
    endif()
endforeach()

message(STATUS "Results: ${PASSED} passed, ${FAILED} failed out of ${TOTAL_TESTS} tests")

if(FAILED GREATER 0)
    message(FATAL_ERROR "Some tests failed")
endif()
