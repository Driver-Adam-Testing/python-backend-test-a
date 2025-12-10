#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>
#include <functional>

// Helper functions and classes for testing
int add(int a, int b) { return a + b; }
double multiply(double a, double b) { return a * b; }
void printMessage(const std::string& msg) { std::cout << msg << std::endl; }

template<typename T>
T maximum(T a, T b) { return (a > b) ? a : b; }

namespace Math {
    double square(double x) { return x * x; }
    double power(double base, double exp) { return std::pow(base, exp); }

    namespace Advanced {
        double logarithm(double x) { return std::log(x); }
    }
}

class Calculator {
private:
    double value;

public:
    Calculator(double v = 0.0) : value(v) {}

    double getValue() const { return value; }
    void setValue(double v) { value = v; }

    Calculator add(double x) { value += x; return *this; }
    Calculator multiply(double x) { value *= x; return *this; }

    Calculator operator+(const Calculator& other) const {
        return Calculator(value + other.value);
    }

    Calculator operator-(const Calculator& other) const {
        return Calculator(value - other.value);
    }

    Calculator& operator++() { ++value; return *this; }
    Calculator operator++(int) { Calculator temp(*this); ++value; return temp; }

    double operator()(double x, double y) const { return value + x + y; }

    static Calculator createZero() { return Calculator(0.0); }
    static Calculator createOne() { return Calculator(1.0); }
};

template<typename T>
class Container {
private:
    T data;

public:
    Container(const T& d) : data(d) {}

    T get() const { return data; }
    void set(const T& d) { data = d; }

    template<typename U>
    void convertFrom(const U& value) { data = static_cast<T>(value); }
};

class Base {
public:
    virtual void virtualMethod() { std::cout << "Base virtual method" << std::endl; }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void virtualMethod() override { std::cout << "Derived virtual method" << std::endl; }
    void derivedMethod() { std::cout << "Derived specific method" << std::endl; }
};

int main() {
    // 1. Basic function calls
    int sum = add(5, 3);
    double product = multiply(2.5, 4.0);
    printMessage("Hello, World!");

    // 2. Template function calls
    int max_int = maximum(10, 20);
    double max_double = maximum(3.14, 2.71);
    std::string max_string = maximum(std::string("apple"), std::string("banana"));

    // 3. Namespace qualified calls
    double squared = Math::square(5.0);
    double powered = Math::power(2.0, 8.0);
    double log_value = Math::Advanced::logarithm(10.0);

    // 4. Member function calls
    Calculator calc(10.0);
    double current_value = calc.getValue();
    calc.setValue(20.0);

    // 5. Method chaining
    Calculator chained_calc;
    chained_calc.add(5.0).multiply(2.0).add(3.0);

    // 6. Static method calls
    Calculator zero_calc = Calculator::createZero();
    Calculator one_calc = Calculator::createOne();

    // 7. Operator calls (function call syntax)
    Calculator calc1(15.0);
    Calculator calc2(25.0);
    Calculator sum_calc = calc1 + calc2;
    Calculator diff_calc = calc1 - calc2;

    // 8. Increment/decrement operator calls
    ++calc1;  // Pre-increment
    calc2++;  // Post-increment

    // 9. Function call operator
    double result = calc1(5.0, 10.0);

    // 10. Constructor calls
    Calculator constructed_calc(100.0);
    Calculator copy_constructed(constructed_calc);
    Calculator default_constructed;

    // 11. Template class method calls
    Container<int> int_container(42);
    int stored_value = int_container.get();
    int_container.set(84);
    int_container.convertFrom(3.14);  // Template member function

    Container<std::string> string_container(std::string("Hello"));
    std::string stored_string = string_container.get();
    string_container.convertFrom(123);  // Converts int to string

    // 12. STL function calls
    std::vector<int> numbers = {5, 2, 8, 1, 9};

    // STL algorithm calls
    std::sort(numbers.begin(), numbers.end());
    auto it = std::find(numbers.begin(), numbers.end(), 8);
    int count = std::count_if(numbers.begin(), numbers.end(), [](int x) { return x > 5; });

    // Container method calls
    numbers.push_back(100);
    numbers.pop_back();
    size_t size = numbers.size();
    bool empty = numbers.empty();

    // 13. Iterator calls
    auto begin_it = numbers.begin();
    auto end_it = numbers.end();

    for (auto it = begin_it; it != end_it; ++it) {
        std::cout << *it << " ";
    }

    // 14. Lambda function calls
    auto lambda_add = [](int a, int b) { return a + b; };
    int lambda_result = lambda_add(10, 20);

    auto capture_lambda = [&numbers](int value) {
        numbers.push_back(value);
    };
    capture_lambda(999);

    // 15. std::function calls
    std::function<int(int, int)> func_obj = add;
    int func_result = func_obj(7, 13);

    func_obj = lambda_add;
    int lambda_func_result = func_obj(3, 4);

    // 16. Function pointer calls
    int (*ptr_to_add)(int, int) = add;
    int ptr_result = ptr_to_add(100, 200);

    // 17. Virtual function calls
    std::unique_ptr<Base> base_ptr = std::make_unique<Derived>();
    base_ptr->virtualMethod();  // Calls Derived::virtualMethod due to polymorphism

    Derived derived_obj;
    derived_obj.virtualMethod();
    derived_obj.derivedMethod();

    // 18. Smart pointer method calls
    std::shared_ptr<Calculator> shared_calc = std::make_shared<Calculator>(50.0);
    double shared_value = shared_calc->getValue();
    shared_calc->setValue(75.0);

    std::unique_ptr<Calculator> unique_calc = std::make_unique<Calculator>(30.0);
    double unique_value = unique_calc->getValue();

    // 19. Type conversion calls
    double pi = 3.14159;
    int truncated_pi = static_cast<int>(pi);
    auto auto_truncated = static_cast<long>(pi);

    // 20. Explicit constructor calls
    Calculator explicit_calc = Calculator(666.0);
    std::string explicit_string = std::string("Explicit String");
    std::vector<int> explicit_vector = std::vector<int>(5, 100);  // 5 elements, all 100

    // 21. Placement new calls (advanced)
    alignas(Calculator) char buffer[sizeof(Calculator)];
    Calculator* placed_calc = new(buffer) Calculator(777.0);
    placed_calc->setValue(888.0);
    placed_calc->~Calculator();  // Explicit destructor call

    // 22. Member function calls through pointers
    Calculator calc_for_ptr(123.0);
    double (Calculator::*get_method)() const = &Calculator::getValue;
    void (Calculator::*set_method)(double) = &Calculator::setValue;

    double ptr_method_result = (calc_for_ptr.*get_method)();
    (calc_for_ptr.*set_method)(456.0);

    Calculator* calc_ptr = &calc_for_ptr;
    double ptr_arrow_result = (calc_ptr->*get_method)();
    (calc_ptr->*set_method)(789.0);

    // 23. Recursive function calls
    std::function<int(int)> fibonacci = [&fibonacci](int n) -> int {
        return (n <= 1) ? n : fibonacci(n - 1) + fibonacci(n - 2);
    };
    int fib_result = fibonacci(10);

    // 24. Variadic template function calls
    auto variadic_print = [](auto&&... args) {
        ((std::cout << args << " "), ...);
        std::cout << std::endl;
    };
    variadic_print("Hello", 42, 3.14, "World");

    // 25. Exception-related calls
    try {
        throw std::runtime_error("Test exception");
    } catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }

    // 26. RAII and automatic destructor calls
    {
        Calculator scoped_calc(999.0);
        scoped_calc.setValue(111.0);
    }  // Destructor called automatically here

    // 27. Perfect forwarding calls
    auto forward_call = [](auto&& func, auto&&... args) {
        return std::forward<decltype(func)>(func)(std::forward<decltype(args)>(args)...);
    };

    int forwarded_result = forward_call(add, 15, 25);

    // 28. Conditional function calls
    bool condition = true;
    int conditional_result = condition ? add(1, 2) : multiply(3, 4);

    // 29. Function calls in expressions
    int complex_expression = add(multiply(2, 3), Math::square(4)) + maximum(10, 20);

    // 30. Method calls with type deduction
    auto deduced_calc = Calculator::createZero();
    auto deduced_value = deduced_calc.getValue();
    deduced_calc.setValue(auto_truncated);

    return 0;
}
