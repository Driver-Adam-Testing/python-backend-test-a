#include <iostream>
#include <string>

// 1. Basic C-style enum
enum Color {
    RED,
    GREEN,
    BLUE
};

// 2. Enum with explicit values
enum StatusCode {
    SUCCESS = 0,
    ERROR_FILE_NOT_FOUND = 404,
    ERROR_PERMISSION_DENIED = 403,
    ERROR_INTERNAL = 500
};

// 3. Enum with specified underlying type
enum class Priority : int {
    LOW = 1,
    MEDIUM = 5,
    HIGH = 10,
    CRITICAL = 20
};

// 4. Scoped enum (enum class) - C++11
enum class Direction {
    NORTH,
    SOUTH,
    EAST,
    WEST
};

// 5. Strongly typed enum with char underlying type
enum class Grade : char {
    A = 'A',
    B = 'B',
    C = 'C',
    D = 'D',
    F = 'F'
};

// 6. Anonymous enum for constants
enum {
    BUFFER_SIZE = 1024,
    MAX_CONNECTIONS = 100,
    TIMEOUT_SECONDS = 30
};

// 7. Forward declared enum
enum class NetworkState : unsigned char;

// 8. Enum in namespace
namespace Graphics {
    enum RenderMode {
        WIREFRAME,
        SOLID,
        TEXTURED,
        RAYTRACED
    };

    enum class BlendMode : int {
        NORMAL = 0,
        MULTIPLY = 1,
        SCREEN = 2,
        OVERLAY = 3,
        SOFT_LIGHT = 4,
        HARD_LIGHT = 5
    };
}

// 9. Enum used in class
class GameEntity {
public:
    enum EntityType {
        PLAYER,
        ENEMY,
        NPC,
        ITEM,
        OBSTACLE
    };

    enum class MovementType : unsigned char {
        STATIC,
        LINEAR,
        CURVED,
        RANDOM,
        AI_CONTROLLED
    };

private:
    EntityType type;
    MovementType movement;

public:
    GameEntity(EntityType t, MovementType m) : type(t), movement(m) {}

    EntityType getType() const { return type; }
    MovementType getMovementType() const { return movement; }
};

// 10. Template with enum parameter
template<Priority P>
class Task {
public:
    static constexpr Priority getPriority() {
        return P;
    }

    void execute() {
        std::cout << "Executing task with priority: " << static_cast<int>(P) << std::endl;
    }
};

// 11. Enum with bit flags (common pattern)
enum FilePermissions {
    NONE = 0,
    READ = 1,
    WRITE = 2,
    EXECUTE = 4,
    READ_WRITE = READ | WRITE,
    ALL = READ | WRITE | EXECUTE
};

// 12. Scoped enum with bit flags
enum class AccessFlags : unsigned int {
    NONE = 0u,
    READ = 1u,
    WRITE = 2u,
    EXECUTE = 4u,
    DELETE = 8u,
    CREATE = 16u,
    MODIFY = 32u,
    FULL_ACCESS = READ | WRITE | EXECUTE | DELETE | CREATE | MODIFY
};

// Operator overloads for bit flag operations
AccessFlags operator|(AccessFlags lhs, AccessFlags rhs) {
    return static_cast<AccessFlags>(
        static_cast<unsigned int>(lhs) | static_cast<unsigned int>(rhs)
    );
}

AccessFlags operator&(AccessFlags lhs, AccessFlags rhs) {
    return static_cast<AccessFlags>(
        static_cast<unsigned int>(lhs) & static_cast<unsigned int>(rhs)
    );
}

// 13. Definition of forward declared enum
enum class NetworkState : unsigned char {
    DISCONNECTED = 0,
    CONNECTING = 1,
    CONNECTED = 2,
    ERROR = 255
};

// 14. Nested enum in template class
template<typename T>
class Container {
public:
    enum InsertionPolicy {
        REPLACE_EXISTING,
        IGNORE_DUPLICATES,
        APPEND_ALWAYS
    };

    enum class SortOrder {
        ASCENDING,
        DESCENDING,
        NONE
    };

private:
    InsertionPolicy policy;
    SortOrder order;

public:
    Container(InsertionPolicy p = REPLACE_EXISTING, SortOrder o = SortOrder::NONE)
        : policy(p), order(o) {}
};

// 15. Enum used in function signatures
std::string colorToString(Color color) {
    switch (color) {
        case RED: return "Red";
        case GREEN: return "Green";
        case BLUE: return "Blue";
        default: return "Unknown";
    }
}

Direction getOppositeDirection(Direction dir) {
    switch (dir) {
        case Direction::NORTH: return Direction::SOUTH;
        case Direction::SOUTH: return Direction::NORTH;
        case Direction::EAST: return Direction::WEST;
        case Direction::WEST: return Direction::EAST;
        default: return Direction::NORTH;  // Should never reach here
    }
}

// 16. Enum class with methods (via free functions)
constexpr bool isValidGrade(Grade g) {
    return g >= Grade::F && g <= Grade::A;
}

double gradeToGPA(Grade g) {
    switch (g) {
        case Grade::A: return 4.0;
        case Grade::B: return 3.0;
        case Grade::C: return 2.0;
        case Grade::D: return 1.0;
        case Grade::F: return 0.0;
        default: return 0.0;
    }
}

// 17. Using enum in constexpr context
constexpr Priority getDefaultPriority() {
    return Priority::MEDIUM;
}

constexpr int getPriorityValue(Priority p) {
    return static_cast<int>(p);
}

// 18. Enum used with std::underlying_type
#include <type_traits>

template<typename E>
constexpr auto toUnderlying(E e) noexcept {
    return static_cast<std::underlying_type_t<E>>(e);
}

// 19. Conditional compilation with enums
#ifdef DEBUG_MODE
enum DebugLevel {
    DEBUG_NONE,
    DEBUG_BASIC,
    DEBUG_VERBOSE,
    DEBUG_FULL
};
#endif

// 20. Multiple enums in single statement (C-style)
enum WeekDay {
    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY
}, WeekEnd {
    SATURDAY, SUNDAY
};

int main() {
    // Using basic enum
    Color favorite_color = RED;
    std::cout << "Favorite color: " << colorToString(favorite_color) << std::endl;

    // Using scoped enum
    Direction current_direction = Direction::NORTH;
    Direction opposite = getOppositeDirection(current_direction);

    // Using enum with explicit values
    StatusCode result = SUCCESS;
    if (result == SUCCESS) {
        std::cout << "Operation completed successfully" << std::endl;
    }

    // Using enum class with underlying type
    Priority task_priority = Priority::HIGH;
    std::cout << "Task priority value: " << static_cast<int>(task_priority) << std::endl;

    // Using Grade enum
    Grade student_grade = Grade::A;
    std::cout << "Student GPA: " << gradeToGPA(student_grade) << std::endl;

    // Using anonymous enum constants
    char buffer[BUFFER_SIZE];
    std::cout << "Buffer size: " << BUFFER_SIZE << std::endl;

    // Using namespaced enum
    Graphics::RenderMode render_mode = Graphics::TEXTURED;
    Graphics::BlendMode blend_mode = Graphics::BlendMode::MULTIPLY;

    // Using enum in class
    GameEntity player(GameEntity::PLAYER, GameEntity::MovementType::AI_CONTROLLED);
    std::cout << "Player type: " << player.getType() << std::endl;

    // Using template with enum
    Task<Priority::HIGH> high_priority_task;
    high_priority_task.execute();

    // Using bit flag enums
    FilePermissions file_perms = READ_WRITE;
    AccessFlags access_flags = AccessFlags::READ | AccessFlags::WRITE;

    // Using with underlying type helper
    std::cout << "Direction underlying value: " << toUnderlying(current_direction) << std::endl;

    // Using container with enum
    Container<int> int_container(Container<int>::REPLACE_EXISTING, Container<int>::SortOrder::ASCENDING);

    return 0;
}
