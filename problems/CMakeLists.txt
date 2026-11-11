# Discover complete numeric problem folders; no per-problem registration needed.
file(GLOB PROBLEM_CMAKE_FILES CONFIGURE_DEPENDS
    RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
    "[0-9]*/CMakeLists.txt"
)
list(SORT PROBLEM_CMAKE_FILES)

foreach(PROBLEM_CMAKE IN LISTS PROBLEM_CMAKE_FILES)
    get_filename_component(PROBLEM_ID "${PROBLEM_CMAKE}" DIRECTORY)
    if(PROBLEM_ID MATCHES "^[1-9][0-9]*$"
       AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${PROBLEM_ID}/main.cpp")
        add_subdirectory("${PROBLEM_ID}")
    endif()
endforeach()
