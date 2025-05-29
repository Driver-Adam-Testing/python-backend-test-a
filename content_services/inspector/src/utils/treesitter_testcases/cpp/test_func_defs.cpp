#include <iostream>
#include <string>
#include <vector>

// 1. Basic function definitions
int add(int a, int b) {
    return a + b;
}

void printMessage(const std::string& message) {
    std::cout << message << std::endl;
}

// 2. Function with default parameters
double multiply(double a, double b = 1.0) {
    return a * b;
}

// 3. Function with auto return type
auto divide(double a, double b) -> double {
    return a / b;
}

// 4. Template function
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

// 5. Constexpr function
constexpr int fibonacci(int n) {
    return (n <= 1) ? n : fibonacci(n - 1) + fibonacci(n - 2);
}

// 6. Inline function
inline int square(int x) {
    return x * x;
}

// 7. Function with reference parameters
void swap(int& a, int& b) {
    int temp = a;
    a = b;
    b = temp;
}

// 8. Function with rvalue reference (move semantics)
void processVector(std::vector<int>&& vec) {
    // Process the moved vector
}

// 9. Namespace scoped functions
namespace MathUtils {
    double calculateArea(double radius) {
        return 3.14159 * radius * radius;
    }

    namespace Advanced {
        double complexCalculation(double x, double y) {
            return x * y + calculateArea(x);
        }
    }
}

// 10. Class definitions with various member functions
class Calculator {
private:
    double value;

public:
    // Default constructor
    Calculator() : value(0.0) {}

    // Parameterized constructor
    Calculator(double initial_value) : value(initial_value) {}

    // Copy constructor
    Calculator(const Calculator& other) : value(other.value) {}

    // Move constructor
    Calculator(Calculator&& other) noexcept : value(other.value) {
        other.value = 0.0;
    }

    // Destructor
    ~Calculator() {}

    // Copy assignment operator
    Calculator& operator=(const Calculator& other) {
        if (this != &other) {
            value = other.value;
        }
        return *this;
    }

    // Move assignment operator
    Calculator& operator=(Calculator&& other) noexcept {
        if (this != &other) {
            value = other.value;
            other.value = 0.0;
        }
        return *this;
    }

    // Regular member function
    double getValue() const {
        return value;
    }

    // Member function with parameters
    void setValue(double new_value) {
        value = new_value;
    }

    // Arithmetic operator overloads
    Calculator operator+(const Calculator& other) const {
        return Calculator(value + other.value);
    }

    Calculator operator-(const Calculator& other) const {
        return Calculator(value - other.value);
    }

    Calculator operator*(const Calculator& other) const {
        return Calculator(value * other.value);
    }

    Calculator operator/(const Calculator& other) const {
        return Calculator(value / other.value);
    }

    // Unary operator
    Calculator operator-() const {
        return Calculator(-value);
    }

    // Increment/decrement operators
    Calculator& operator++() {  // Pre-increment
        ++value;
        return *this;
    }

    Calculator operator++(int) {  // Post-increment
        Calculator temp(*this);
        ++value;
        return temp;
    }

    // Comparison operators
    bool operator==(const Calculator& other) const {
        return value == other.value;
    }

    bool operator!=(const Calculator& other) const {
        return !(*this == other);
    }

    bool operator<(const Calculator& other) const {
        return value < other.value;
    }

    // Function call operator
    double operator()(double x, double y) {
        return x + y + value;
    }

    // Array subscript operator
    double operator[](int index) {
        return value * index;
    }

    // Static member function
    static Calculator createZero() {
        return Calculator(0.0);
    }
};

// 11. Template class with member functions
template<typename T>
class Container {
private:
    T data;

public:
    Container(const T& initial_data) : data(initial_data) {}

    T getData() const {
        return data;
    }

    void setData(const T& new_data) {
        data = new_data;
    }

    template<typename U>
    void convertAndSet(const U& value) {
        data = static_cast<T>(value);
    }
};

// 12. Inheritance and virtual functions
class Shape {
public:
    virtual ~Shape() = default;
    virtual double calculateArea() const = 0;  // Pure virtual
    virtual void draw() const {  // Virtual with default implementation
        std::cout << "Drawing a shape" << std::endl;
    }
};

class Circle : public Shape {
private:
    double radius;

public:
    Circle(double r) : radius(r) {}

    double calculateArea() const override {
        return 3.14159 * radius * radius;
    }

    void draw() const override {
        std::cout << "Drawing a circle with radius " << radius << std::endl;
    }
};

class Rectangle : public Shape {
private:
    double width, height;

public:
    Rectangle(double w, double h) : width(w), height(h) {}

    double calculateArea() const override {
        return width * height;
    }

    void draw() const override {
        std::cout << "Drawing a rectangle " << width << "x" << height << std::endl;
    }
};

// 13. Function definitions outside class (qualified names)
double MathUtils::Advanced::complexCalculation(double x, double y);  // Already defined above

// 14. Lambda expressions in functions
void demonstrateLambdas() {
    auto simpleLambda = []() {
        std::cout << "Simple lambda" << std::endl;
    };

    auto lambdaWithCapture = [&](int x) -> int {
        return x * 2;
    };

    auto lambdaWithMutableCapture = [=](int y) mutable -> int {
        return y + 10;
    };
}

// 15. Function try blocks
Calculator safeDivide(double a, double b) try {
    if (b == 0.0) {
        throw std::runtime_error("Division by zero");
    }
    return Calculator(a / b);
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return Calculator(0.0);
}

// 16. Specialized template functions
template<>
bool maximum<bool>(bool a, bool b) {
    return a || b;
}

// 17. Friend functions
class Point {
private:
    double x, y;

public:
    Point(double x_val, double y_val) : x(x_val), y(y_val) {}

    friend Point operator+(const Point& lhs, const Point& rhs) {
        return Point(lhs.x + rhs.x, lhs.y + rhs.y);
    }

    friend std::ostream& operator<<(std::ostream& os, const Point& point) {
        os << "(" << point.x << ", " << point.y << ")";
        return os;
    }
};

// 18. Main function
int main() {
    Calculator calc1(10.0);
    Calculator calc2(5.0);
    Calculator result = calc1 + calc2;

    auto lambda = [](int x) { return x * x; };
    int squared = lambda(5);

    Circle circle(5.0);
    Rectangle rect(4.0, 6.0);

    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(3.0));
    shapes.push_back(std::make_unique<Rectangle>(2.0, 8.0));

    for (const auto& shape : shapes) {
        shape->draw();
        std::cout << "Area: " << shape->calculateArea() << std::endl;
    }

    return 0;
}
