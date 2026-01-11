package com.example;

public class MethodExamples {

    // Constructor
    public MethodExamples() {

    }

    // Static method
    public static void staticMethod() {
        System.out.println("Static method");
    }

    // Instance method with parameters
    public String processData(String input, int count) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < count; i++) {
            result.append(input);
        }
        return result.toString();
    }

    // Private method
    private void privateHelper() {
        // Implementation
    }

    // Method with generic parameters
    public <T> List<T> createList(T... items) {
        return Arrays.asList(items);
    }

    // Override method
    @Override
    public String toString() {
        return "MethodExamples";
    }
}
