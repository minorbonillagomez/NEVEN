project(PB)

add_library(PB STATIC variable.pb.cc)

target_include_directories(PB PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(PB PRIVATE libprotobuf)
