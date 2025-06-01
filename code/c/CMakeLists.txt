cmake_minimum_required(VERSION 3.25)
project(simple_query C)

add_library(cjson lib/cJSON.c
        lib/cJSON.h)

set(CMAKE_C_STANDARD 23)

# Find required packages
find_package(SQLite3 REQUIRED)
find_package(Ulfius REQUIRED)  # Add this line

add_executable(simple_query main.c)

target_include_directories(simple_query PRIVATE
        /home/webmaster/simple_query/lib
        ${ULFIUS_INCLUDE_DIRS}  # Add this line
)

target_link_libraries(simple_query PRIVATE
        SQLite::SQLite3
        cjson
        ulfius
)
