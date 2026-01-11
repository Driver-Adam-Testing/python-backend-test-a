package com.example;

import java.util.List;
import java.util.ArrayList;

/**
 * A simple class demonstrating Java features
 */
public class TestClass {
    private int value;
    private static final String CONSTANT = "test";

    public TestClass(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }

    public void setValue(int value) {
        this.value = value;
    }

    public static class InnerClass {
        private String name;

        public InnerClass(String name) {
            this.name = name;
        }
    }
}

abstract class AbstractClass {
    protected abstract void doSomething();
}

class ConcreteClass extends AbstractClass implements Comparable<ConcreteClass> {
    @Override
    protected void doSomething() {
        System.out.println("Doing something");
    }

    @Override
    public int compareTo(ConcreteClass other) {
        return 0;
    }
}
