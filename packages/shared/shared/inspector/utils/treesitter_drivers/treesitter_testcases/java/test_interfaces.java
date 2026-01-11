package com.example;

/**
 * Interface demonstrating Java interface features
 */
public interface Drawable {
    // Constant (implicitly public, static, final)
    String DEFAULT_COLOR = "black";

    // Abstract method (implicitly public and abstract)
    void draw();

    // Default method (Java 8+)
    default void setColor(String color) {
        System.out.println("Setting color to: " + color);
    }

    // Static method (Java 8+)
    static void info() {
        System.out.println("This is a drawable interface");
    }
}

interface Resizable extends Drawable {
    void resize(int width, int height);

    // Nested interface
    interface ResizeListener {
        void onResize(int oldWidth, int oldHeight, int newWidth, int newHeight);
    }
}

// Functional interface
@FunctionalInterface
interface Calculator {
    int calculate(int a, int b);
}
