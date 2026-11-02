cmake_minimum_required(VERSION 3.16)

project(Elusion-TP5 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

include(FetchContent)

FetchContent_Declare(
    argparse
    GIT_REPOSITORY https://github.com/p-ranav/argparse.git
    GIT_TAG v3.2
)

FetchContent_MakeAvailable(argparse)

add_library(libs STATIC
    src/utils/sfm.cpp
)

# Add include directories to a target.
target_include_directories(libs PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/utils/include
)


add_executable(ElusionSIM
    src/main.cpp
)

target_link_libraries(ElusionSIM PRIVATE
    libs
    argparse
)

