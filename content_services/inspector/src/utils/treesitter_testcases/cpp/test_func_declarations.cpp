#include <iostream>
#include <string>
#include <vector>
#include <memory>

// 1. Basic function declarations
int add(int a, int b);
double multiply(double a, double b);
void printMessage(const std::string& message);
std::string concatenate(const std::string& first, const std::string& second);

// 2. Function declarations with default parameters
double divide(double numerator, double denominator = 1.0);
void setupConnection(const std::string& host = "localhost", int port = 8080, bool secure = false);

// 3. Function declarations with const and reference parameters
void processData(const std::vector<int>& data);
void swapValues(int& first, int& second);
void processString(const std::string& input, std::string& output);

// 4. Function declarations with rvalue references (C++11)
void processVector(std::vector<int>&& data);
std::string moveString(std::string&& input);

// 5. Template function declarations
template<typename T>
T maximum(const T& a, const T& b);

template<typename T, typename U>
auto addValues(const T& first, const U& second) -> decltype(first + second);

template<class Iterator, class Predicate>
bool allOf(Iterator first, Iterator last, Predicate pred);

// 6. Template function with multiple template parameters
template<typename ReturnType, typename... Args>
ReturnType callFunction(ReturnType(*func)(Args...), Args... args);

// 7. Constexpr function declarations
constexpr int factorial(int n);
constexpr double calculateCircleArea(double radius);

// 8. Inline function declarations
inline int square(int x);
inline double cube(double x);

// 9. Noexcept function declarations (C++11)
void safeFunction() noexcept;
int safeMath(int a, int b) noexcept;
void conditionalNoexcept(bool condition) noexcept(true);

// 10. Function declarations with auto return type (C++14)
auto detectType(int value) -> int;
auto computeValue(double input);

// 11. Namespace function declarations
namespace Math {
    double sin(double angle);
    double cos(double angle);
    double pow(double base, double exponent);

    namespace Advanced {
        double integrate(double(*func)(double), double start, double end);
        std::vector<double> solve(const std::vector<double>& coefficients);
    }
}

// 12. Class member function declarations
class Calculator {
private:
    double value;

public:
    // Constructor declarations
    Calculator();
    Calculator(double initial_value);
    Calculator(const Calculator& other);
    Calculator(Calculator&& other) noexcept;

    // Destructor declaration
    ~Calculator();

    // Assignment operator declarations
    Calculator& operator=(const Calculator& other);
    Calculator& operator=(Calculator&& other) noexcept;

    // Member function declarations
    double getValue() const;
    void setValue(double new_value);
    void reset();

    // Const member function declarations
    bool isZero() const;
    bool isPositive() const noexcept;
    std::string toString() const;

    // Static member function declarations
    static Calculator createZero();
    static Calculator createFromString(const std::string& value);
    static bool isValidValue(double value) noexcept;

    // Operator overload declarations
    Calculator operator+(const Calculator& other) const;
    Calculator operator-(const Calculator& other) const;
    Calculator operator*(const Calculator& other) const;
    Calculator operator/(const Calculator& other) const;

    Calculator& operator+=(const Calculator& other);
    Calculator& operator-=(const Calculator& other);
    Calculator& operator*=(const Calculator& other);
    Calculator& operator/=(const Calculator& other);

    Calculator& operator++();          // Pre-increment
    Calculator operator++(int);        // Post-increment

    Calculator operator-() const;      // Unary minus
    Calculator operator+() const;      // Unary plus

    bool operator==(const Calculator& other) const;
    bool operator!=(const Calculator& other) const;
    bool operator<(const Calculator& other) const;
    bool operator<=(const Calculator& other) const;
    bool operator>(const Calculator& other) const;
    bool operator>=(const Calculator& other) const;

    double operator()(double x, double y) const;   // Function call operator
    double& operator[](size_t index);              // Array subscript operator
    const double& operator[](size_t index) const;

    // Conversion operator declarations
    operator double() const;
    operator bool() const;
    explicit operator int() const;
};

// 13. Template class member function declarations
template<typename T>
class Container {
private:
    T data;

public:
    Container();
    explicit Container(const T& initial_data);
    Container(const Container<T>& other);
    Container(Container<T>&& other) noexcept;

    ~Container();

    Container<T>& operator=(const Container<T>& other);
    Container<T>& operator=(Container<T>&& other) noexcept;

    T get() const;
    void set(const T& new_data);
    void clear();

    bool empty() const noexcept;
    size_t size() const noexcept;

    template<typename U>
    void convertFrom(const U& value);

    template<typename U>
    Container<U> convertTo() const;

    // Template member function declarations
    template<typename Function>
    auto apply(Function func) -> decltype(func(data));

    template<typename Predicate>
    bool satisfies(Predicate pred) const;
};

// 14. Friend function declarations
class Point {
private:
    double x, y;

public:
    Point(double x_val, double y_val);

    // Friend function declarations
    friend Point operator+(const Point& lhs, const Point& rhs);
    friend Point operator-(const Point& lhs, const Point& rhs);
    friend Point operator*(const Point& point, double scalar);
    friend Point operator*(double scalar, const Point& point);

    friend bool operator==(const Point& lhs, const Point& rhs);
    friend bool operator!=(const Point& lhs, const Point& rhs);

    friend std::ostream& operator<<(std::ostream& os, const Point& point);
    friend std::istream& operator>>(std::istream& is, Point& point);

    friend double distance(const Point& p1, const Point& p2);
    friend Point midpoint(const Point& p1, const Point& p2);
};

// 15. Virtual function declarations
class Shape {
public:
    Shape();
    virtual ~Shape() = default;

    virtual double getArea() const = 0;         // Pure virtual
    virtual double getPerimeter() const = 0;    // Pure virtual
    virtual void draw() const;                  // Virtual with implementation
    virtual std::string getType() const;        // Virtual

    // Virtual operator declarations
    virtual bool operator==(const Shape& other) const;
    virtual Shape* clone() const = 0;
};

class Circle : public Shape {
private:
    double radius;

public:
    Circle(double r);

    double getArea() const override;
    double getPerimeter() const override;
    void draw() const override;
    std::string getType() const override;

    bool operator==(const Shape& other) const override;
    Shape* clone() const override;

    // Circle-specific declarations
    double getRadius() const;
    void setRadius(double new_radius);
    double val;
};

// 16. Function template specialization declarations
template<>
bool maximum<bool>(const bool& a, const bool& b);

template<>
std::string maximum<std::string>(const std::string& a, const std::string& b);

// 17. Operator overload declarations (global)
Calculator operator+(double lhs, const Calculator& rhs);
Calculator operator-(double lhs, const Calculator& rhs);
Calculator operator*(double lhs, const Calculator& rhs);
Calculator operator/(double lhs, const Calculator& rhs);

std::ostream& operator<<(std::ostream& os, const Calculator& calc);
std::istream& operator>>(std::istream& is, Calculator& calc);

// 18. Function pointer and std::function declarations
typedef int (*BinaryIntFunction)(int, int);
typedef void (*VoidFunction)();

using StringProcessor = std::function<std::string(const std::string&)>;
using Predicate = std::function<bool(int)>;

// Function declarations that take function pointers
int applyBinaryFunction(BinaryIntFunction func, int a, int b);
void executeCallback(VoidFunction callback);
std::string processWithFunction(const std::string& input, StringProcessor processor);

// 19. Variadic template function declarations
template<typename... Args>
void print(Args... args);

template<typename T, typename... Args>
std::unique_ptr<T> makeUnique(Args&&... args);

template<typename Function, typename... Args>
auto invoke(Function&& func, Args&&... args) -> decltype(func(args...));

// 20. Consteval and constinit function declarations (C++20)
#if __cplusplus >= 202002L
consteval int compileTimeCalculation(int x);
constinit int globalInitialization();
#endif

// 21. Coroutine function declarations (C++20)
#if __cplusplus >= 202002L
#include <coroutine>
std::generator<int> generateNumbers(int start, int end);
std::task<void> asyncOperation();
std::task<std::string> fetchData(const std::string& url);
#endif

// 22. Concept-constrained function declarations (C++20)
#if __cplusplus >= 202002L
template<std::integral T>
T gcd(T a, T b);

template<std::floating_point T>
T sqrt(T value);

template<typename Container>
requires std::ranges::range<Container>
void processRange(Container& container);
#endif

// 23. Function declarations with attributes
[[nodiscard]] int importantFunction();
[[deprecated("Use newFunction instead")]] void oldFunction();
[[maybe_unused]] static void debugFunction();

// 24. Exception specification declarations (legacy, but might be found in old code)
#ifndef __cpp_noexcept_function_type
void legacyFunction() throw();
void legacyFunctionWithExceptions() throw(std::runtime_error, std::logic_error);
#endif

// 25. External "C" linkage declarations
extern "C" {
    int c_style_function(int x, int y);
    void c_style_callback(void (*callback)(int));
}

// 26. Lambda declarations (stored in variables)
extern const auto global_lambda;
extern std::function<int(int, int)> global_function_object;

// 27. Thread-local function declarations
thread_local std::string getThreadId();
thread_local void setThreadData(const std::string& data);

// Some minimal definitions to avoid linker errors
int add(int a, int b) { return a + b; }
double multiply(double a, double b) { return a * b; }
void printMessage(const std::string& message) { std::cout << message << std::endl; }

const auto global_lambda = [](int x, int y) { return x + y; };

int main() {
    // Test some of the declared functions
    int result = add(5, 3);
    double product = multiply(2.5, 4.0);
    printMessage("Testing function declarations");

    Calculator calc(10.0);
    std::cout << "Calculator value: " << calc.getValue() << std::endl;

    return 0;
}
