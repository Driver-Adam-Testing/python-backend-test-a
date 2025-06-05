void test_function_calls_as_args() {
    int x = max(strlen("test"), sizeof(int));
    printf("%s has length %d\n", "example", strlen("example"));
}
#ifdef hi
void test_conditional_calls() {
    if (is_valid("test")) {
        process("test");
    } else {
        handle_error("invalid");
    }
}
#endif
