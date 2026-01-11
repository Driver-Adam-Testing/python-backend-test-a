package com.example;

public class VariableExamples {
    // Class variables (static)
    public static final int MAX_SIZE = 100;
    private static String defaultName = "Unknown";

    // Instance variables
    private int id;
    protected String name;
    public boolean active;

    // Local variables in method
    public void localVariables() {
        int localVar = 42;
        String message = "Hello";
        final double PI = 3.14159;

        for (int i = 0; i < 10; i++) {
            String temp = "iteration " + i;
        }
    }
}
