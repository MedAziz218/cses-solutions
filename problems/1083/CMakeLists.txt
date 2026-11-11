add_executable(problem_1083 main.cpp)

add_custom_target(test_1083
    COMMAND "${CMAKE_COMMAND}"
        "-DPROG=$<TARGET_FILE:problem_1083>"
        "-DTEST_DIR=${CMAKE_CURRENT_SOURCE_DIR}"
        "-DBINARY_DIR=${CMAKE_CURRENT_BINARY_DIR}"
        -P "${CMAKE_SOURCE_DIR}/cmake/test_runner.cmake"
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    DEPENDS problem_1083
    COMMENT "Running tests for problem 1083..."
    VERBATIM
)
