package com.example;

/**
 * Simple color enum
 */
public enum Color {
    RED, GREEN, BLUE
}

/**
 * Status enum with constructor and fields
 */
enum Status {
    ACTIVE(1),
    INACTIVE(0);

    private final int value;

    Status(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }
}

/**
 * Complex enum with multiple methods
 */
public enum Priority {
    LOW(1, "Low Priority"),
    MEDIUM(2, "Medium Priority"),
    HIGH(3, "High Priority");

    private final int level;
    private final String description;

    Priority(int level, String description) {
        this.level = level;
        this.description = description;
    }

    public int getLevel() {
        return level;
    }

    public String getDescription() {
        return description;
    }
}
