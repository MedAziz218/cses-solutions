add_executable(problem_1069 main.cpp)

add_custom_target(test_1069
    COMMAND "${CMAKE_COMMAND}"
        "-DPROG=$<TARGET_FILE:problem_1069>"
        "-DTEST_DIR=${CMAKE_CURRENT_SOURCE_DIR}"
        "-DBINARY_DIR=${CMAKE_CURRENT_BINARY_DIR}"
        -P "${CMAKE_SOURCE_DIR}/cmake/test_runner.cmake"
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    DEPENDS problem_1069
    COMMENT "Running tests for problem 1069..."
    VERBATIM
)
