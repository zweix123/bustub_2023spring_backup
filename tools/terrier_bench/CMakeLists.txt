set(TERRIER_BENCH_SOURCES terrier.cpp)
add_executable(terrier-bench ${TERRIER_BENCH_SOURCES})

target_link_libraries(terrier-bench bustub)
set_target_properties(terrier-bench PROPERTIES OUTPUT_NAME bustub-terrier-bench)

set(TERRIER_DEBUG_SOURCES terrier_debug.cpp)
add_executable(terrier-debug ${TERRIER_DEBUG_SOURCES})

target_link_libraries(terrier-debug bustub)
set_target_properties(terrier-debug PROPERTIES OUTPUT_NAME bustub-terrier-debug)
