#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <atomic>
#include <thread>

// 1. Basic global variables
int global_int = 42;
double global_double = 3.14159;
std::string global_string = "Hello, World!";
bool global_flag = true;

// 2. Const and constexpr variables
const int CONST_VALUE = 100;
constexpr double CONSTEXPR_PI = 3.14159265359;
const std::string CONST_STRING = "Immutable String";

// 3. Static global variables
static int static_counter = 0;
static const char* static_message = "Static Message";

// 4. External variables (declared elsewhere)
extern int external_variable;
extern const double external_constant;

// 5. Pointer variables
int* int_pointer = nullptr;
const int* const_int_pointer = &CONST_VALUE;
int* const pointer_to_const = &global_int;
const int* const const_pointer_to_const = &CONST_VALUE;

// 6. Reference variables (must be initialized)
int& int_reference = global_int;
const int& const_reference = CONST_VALUE;

// 7. Auto variables (type deduction)
auto auto_int = 42;
auto auto_double = 3.14;
auto auto_string = std::string("Auto String");
auto auto_vector = std::vector<int>{1, 2, 3, 4, 5};

// 8. Decltype variables
decltype(global_int) decltype_int = 100;
decltype(auto) decltype_auto_var = global_double;

// 9. Array variables
int global_array[10] = {1, 2, 3, 4, 5};
double matrix[3][3] = {{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}};
std::string string_array[] = {"One", "Two", "Three"};

// 10. STL container variables
std::vector<int> global_vector = {10, 20, 30, 40, 50};
std::vector<std::string> string_vector{"Alpha", "Beta", "Gamma"};

// 11. Smart pointer variables
std::unique_ptr<int> unique_int_ptr = std::make_unique<int>(999);
std::shared_ptr<std::string> shared_string_ptr = std::make_shared<std::string>("Shared String");
std::weak_ptr<std::string> weak_string_ptr = shared_string_ptr;

// 12. Thread-related variables
std::atomic<int> atomic_counter{0};
thread_local int thread_local_var = 0;

// 13. Function pointers
int (*function_pointer)(int, int) = nullptr;
auto lambda_var = [](int x, int y) -> int { return x + y; };

// 14. Template variables (C++14)
template<typename T>
constexpr T pi = T(3.14159265358979323846);

// 15. Variables in anonymous namespace
namespace {
    int anonymous_global = 777;
    const double anonymous_constant = 2.71828;
}

// 16. Variables in named namespace
namespace Config {
    const int MAX_CONNECTIONS = 100;
    const std::string DEFAULT_HOST = "localhost";
    int current_connections = 0;

    namespace Database {
        const std::string CONNECTION_STRING = "postgresql://localhost:5432/mydb";
        int query_timeout = 30;
    }
}

// 17. Conditional compilation variables
#ifdef DEBUG_MODE
int debug_level = 3;
const char* debug_output_file = "debug.log";
#endif

#ifndef RELEASE_MODE
static bool enable_logging = true;
#endif

// 18. Macro-defined variables
#define BUFFER_SIZE 4096
#define MAX_RETRIES 3

char global_buffer[BUFFER_SIZE];
int retry_count = MAX_RETRIES;

// 19. Class with static members
class GlobalState {
public:
    static int instance_count;
    static const double VERSION;
    static std::string application_name;

private:
    static bool initialized;
};

// Static member definitions
int GlobalState::instance_count = 0;
const double GlobalState::VERSION = 1.0;
std::string GlobalState::application_name = "MyApplication";
bool GlobalState::initialized = false;

// 20. Template class static members
template<typename T>
class Counter {
public:
    static int count;
    static void increment() { ++count; }
    static int getCount() { return count; }
};

// Template static member definition
template<typename T>
int Counter<T>::count = 0;

// 21. Variables with attributes (C++11)
[[maybe_unused]] int unused_variable = 0;
[[deprecated("Use new_variable instead")]] int old_variable = 123;

// 22. Volatile variables
volatile int volatile_flag = 0;
volatile std::atomic<bool> volatile_atomic_flag{false};

// 23. Bitfield structures
struct Flags {
    unsigned int flag1 : 1;
    unsigned int flag2 : 1;
    unsigned int flag3 : 1;
    unsigned int reserved : 29;
};

Flags global_flags = {0, 1, 0, 0};

// 24. Union variables
union Data {
    int int_value;
    float float_value;
    char char_array[4];
};

Data global_data = {.int_value = 0x12345678};

// 25. Variables with initializer lists
std::vector<std::pair<std::string, int>> key_value_pairs = {
    {"apple", 5},
    {"banana", 3},
    {"cherry", 8}
};

std::vector<std::vector<int>> matrix_vector = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9}
};

// 26. Structured bindings (C++17) - global scope
auto [first_name, last_name, age] = std::make_tuple(std::string("John"), std::string("Doe"), 30);

// 27. Variables with custom types
enum class Color { RED, GREEN, BLUE };
Color current_color = Color::RED;

struct Point {
    double x, y;
    Point(double x_val, double y_val) : x(x_val), y(y_val) {}
};

Point origin{0.0, 0.0};
Point destination{10.0, 20.0};

// 28. Function objects and functors
struct Multiplier {
    int factor;
    Multiplier(int f) : factor(f) {}
    int operator()(int x) const { return x * factor; }
};

Multiplier times_two{2};
Multiplier times_three{3};

// 29. Variables with RAII pattern
class FileHandle {
    FILE* file;
public:
    FileHandle(const char* filename, const char* mode) : file(fopen(filename, mode)) {}
    ~FileHandle() { if (file) fclose(file); }
    FILE* get() const { return file; }
};

// Note: In real code, this would be properly initialized
// FileHandle global_file_handle{"config.txt", "r"};

// 30. Inline variables (C++17)
inline const std::string INLINE_VERSION = "2.0.1";
inline int inline_counter = 0;

void test_function() {
    // This function tests that local variables are not captured
    int local_variable = 999;
    static int static_local = 888;
    const int const_local = 777;
}

int main() {
    // Test basic usage of global variables
    std::cout << "Global int: " << global_int << std::endl;
    std::cout << "Global string: " << global_string << std::endl;
    std::cout << "Const value: " << CONST_VALUE << std::endl;
    std::cout << "Constexpr PI: " << CONSTEXPR_PI << std::endl;

    // Test auto variables
    std::cout << "Auto int: " << auto_int << std::endl;
    std::cout << "Auto string: " << auto_string << std::endl;

    // Test pointer operations
    *int_pointer = 123;  // This would be safe if int_pointer was properly initialized
    std::cout << "Reference value: " << int_reference << std::endl;

    // Test arrays
    std::cout << "Array element: " << global_array[0] << std::endl;
    std::cout << "Matrix element: " << matrix[0][0] << std::endl;

    // Test containers
    std::cout << "Vector size: " << global_vector.size() << std::endl;

    // Test smart pointers
    if (unique_int_ptr) {
        std::cout << "Unique ptr value: " << *unique_int_ptr << std::endl;
    }

    // Test atomic operations
    atomic_counter.store(100);
    std::cout << "Atomic counter: " << atomic_counter.load() << std::endl;

    // Test namespace variables
    std::cout << "Max connections: " << Config::MAX_CONNECTIONS << std::endl;
    std::cout << "DB timeout: " << Config::Database::query_timeout << std::endl;

    // Test static class members
    std::cout << "Instance count: " << GlobalState::instance_count << std::endl;
    std::cout << "Version: " << GlobalState::VERSION << std::endl;

    // Test template static members
    Counter<int>::increment();
    std::cout << "Int counter: " << Counter<int>::getCount() << std::endl;

    // Test template variables
    std::cout << "Pi<double>: " << pi<double> << std::endl;
    std::cout << "Pi<float>: " << pi<float> << std::endl;

    // Test structured bindings
    std::cout << "Name: " << first_name << " " << last_name << ", Age: " << age << std::endl;

    // Test custom types
    std::cout << "Current color: " << static_cast<int>(current_color) << std::endl;
    std::cout << "Origin: (" << origin.x << ", " << origin.y << ")" << std::endl;

    // Test function objects
    std::cout << "Times two of 5: " << times_two(5) << std::endl;
    std::cout << "Times three of 7: " << times_three(7) << std::endl;

    // Test inline variables
    std::cout << "Inline version: " << INLINE_VERSION << std::endl;

    // Test anonymous namespace variables
    std::cout << "Anonymous global: " << anonymous_global << std::endl;

    return 0;
}
