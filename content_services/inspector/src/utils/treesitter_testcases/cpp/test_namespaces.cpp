#include <iostream>
#include <string>
#include <vector>

// 1. Basic namespace
namespace Math {
    const double PI = 3.14159265359;

    double calculateCircleArea(double radius) {
        return PI * radius * radius;
    }

    double square(double x) {
        return x * x;
    }
}

// 2. Nested namespaces (C++17 style)
namespace Graphics::Rendering::OpenGL {
    void initializeContext() {
        std::cout << "Initializing OpenGL context" << std::endl;
    }

    void renderFrame() {
        std::cout << "Rendering OpenGL frame" << std::endl;
    }
}

// 3. Nested namespaces (traditional style)
namespace Network {
    namespace TCP {
        class Socket {
        public:
            void connect(const std::string& address, int port) {
                std::cout << "TCP connecting to " << address << ":" << port << std::endl;
            }
        };

        void sendData(const std::string& data) {
            std::cout << "TCP sending: " << data << std::endl;
        }
    }

    namespace UDP {
        class Socket {
        public:
            void bind(int port) {
                std::cout << "UDP binding to port " << port << std::endl;
            }
        };

        void sendPacket(const std::string& data) {
            std::cout << "UDP sending: " << data << std::endl;
        }
    }
}

// 4. Anonymous namespace (internal linkage)
namespace {
    int internal_counter = 0;

    void incrementCounter() {
        ++internal_counter;
    }

    class InternalHelper {
    public:
        static void doSomething() {
            std::cout << "Internal helper doing something" << std::endl;
        }
    };
}

// 5. Namespace aliases
namespace GL = Graphics::Rendering::OpenGL;
namespace NetTCP = Network::TCP;
namespace NetUDP = Network::UDP;

// 6. Using declarations and directives
using Math::PI;
using Math::square;
using namespace Network::TCP;  // Brings all TCP namespace into scope

// 7. Namespace with templates
namespace Containers {
    template<typename T>
    class Stack {
    private:
        std::vector<T> elements;

    public:
        void push(const T& element) {
            elements.push_back(element);
        }

        T pop() {
            if (elements.empty()) {
                throw std::runtime_error("Stack is empty");
            }
            T result = elements.back();
            elements.pop_back();
            return result;
        }

        bool empty() const {
            return elements.empty();
        }

        size_t size() const {
            return elements.size();
        }
    };

    template<typename T>
    class Queue {
    private:
        std::vector<T> elements;
        size_t front_index;

    public:
        Queue() : front_index(0) {}

        void enqueue(const T& element) {
            elements.push_back(element);
        }

        T dequeue() {
            if (front_index >= elements.size()) {
                throw std::runtime_error("Queue is empty");
            }
            return elements[front_index++];
        }

        bool empty() const {
            return front_index >= elements.size();
        }
    };
}

// 8. Namespace with enums and constants
namespace Constants {
    enum class Units {
        METERS,
        FEET,
        INCHES,
        CENTIMETERS
    };

    namespace Physics {
        const double SPEED_OF_LIGHT = 299792458.0;  // m/s
        const double GRAVITATIONAL_CONSTANT = 6.67430e-11;  // m³/kg·s²
        const double PLANCK_CONSTANT = 6.62607015e-34;  // J·s
    }

    namespace Time {
        const int SECONDS_PER_MINUTE = 60;
        const int MINUTES_PER_HOUR = 60;
        const int HOURS_PER_DAY = 24;
        const int DAYS_PER_WEEK = 7;
    }
}

// 9. Namespace with function overloads
namespace Utils {
    void print(int value) {
        std::cout << "Integer: " << value << std::endl;
    }

    void print(double value) {
        std::cout << "Double: " << value << std::endl;
    }

    void print(const std::string& value) {
        std::cout << "String: " << value << std::endl;
    }

    template<typename T>
    void print(const std::vector<T>& vec) {
        std::cout << "Vector: [";
        for (size_t i = 0; i < vec.size(); ++i) {
            std::cout << vec[i];
            if (i < vec.size() - 1) std::cout << ", ";
        }
        std::cout << "]" << std::endl;
    }
}

// 10. Extending a namespace (reopening)
namespace Math {
    double cube(double x) {
        return x * x * x;
    }

    template<typename T>
    T max(T a, T b) {
        return (a > b) ? a : b;
    }

    class Calculator {
    private:
        double value;

    public:
        Calculator(double initial = 0.0) : value(initial) {}

        Calculator& add(double x) { value += x; return *this; }
        Calculator& subtract(double x) { value -= x; return *this; }
        Calculator& multiply(double x) { value *= x; return *this; }
        Calculator& divide(double x) { value /= x; return *this; }

        double getValue() const { return value; }
    };
}

// 11. Namespace with inline namespace (C++11)
namespace Version {
    inline namespace v2 {
        class API {
        public:
            static void processData() {
                std::cout << "Processing data with API v2" << std::endl;
            }
        };
    }

    namespace v1 {
        class API {
        public:
            static void processData() {
                std::cout << "Processing data with API v1" << std::endl;
            }
        };
    }
}

// 12. Namespace with friend functions
namespace Geometry {
    class Point {
    private:
        double x, y;

    public:
        Point(double x_val, double y_val) : x(x_val), y(y_val) {}

        friend Point operator+(const Point& lhs, const Point& rhs);
        friend std::ostream& operator<<(std::ostream& os, const Point& point);

        double getX() const { return x; }
        double getY() const { return y; }
    };

    Point operator+(const Point& lhs, const Point& rhs) {
        return Point(lhs.x + rhs.x, lhs.y + rhs.y);
    }

    std::ostream& operator<<(std::ostream& os, const Point& point) {
        os << "(" << point.x << ", " << point.y << ")";
        return os;
    }

    double distance(const Point& p1, const Point& p2) {
        double dx = p1.getX() - p2.getX();
        double dy = p1.getY() - p2.getY();
        return std::sqrt(dx * dx + dy * dy);
    }
}

// 13. Conditional namespace compilation
#ifdef FEATURE_EXPERIMENTAL
namespace Experimental {
    void experimentalFeature() {
        std::cout << "This is an experimental feature" << std::endl;
    }

    class ExperimentalClass {
    public:
        void test() {
            std::cout << "Testing experimental functionality" << std::endl;
        }
    };
}
#endif

// 14. Namespace with static members
namespace Database {
    class ConnectionPool {
    private:
        static int max_connections;
        static int current_connections;

    public:
        static bool acquireConnection() {
            if (current_connections < max_connections) {
                ++current_connections;
                return true;
            }
            return false;
        }

        static void releaseConnection() {
            if (current_connections > 0) {
                --current_connections;
            }
        }

        static int getCurrentConnections() {
            return current_connections;
        }
    };

    // Static member definitions
    int ConnectionPool::max_connections = 10;
    int ConnectionPool::current_connections = 0;
}

// 15. Namespace std specialization (common pattern)
namespace std {
    template<>
    struct hash<Geometry::Point> {
        size_t operator()(const Geometry::Point& point) const {
            return hash<double>()(point.getX()) ^ (hash<double>()(point.getY()) << 1);
        }
    };
}

int main() {
    // Using namespace functions
    double area = Math::calculateCircleArea(5.0);
    std::cout << "Circle area: " << area << std::endl;

    // Using namespace alias
    GL::initializeContext();
    GL::renderFrame();

    // Using namespace classes
    Network::TCP::Socket tcp_socket;
    tcp_socket.connect("localhost", 8080);

    Network::UDP::Socket udp_socket;
    udp_socket.bind(9090);

    // Using using declarations (PI and square are in scope)
    double circle_area = PI * square(3.0);
    std::cout << "Area using 'using' declarations: " << circle_area << std::endl;

    // Using anonymous namespace
    incrementCounter();
    InternalHelper::doSomething();

    // Using template classes from namespace
    Containers::Stack<int> int_stack;
    int_stack.push(10);
    int_stack.push(20);
    std::cout << "Stack size: " << int_stack.size() << std::endl;

    Containers::Queue<std::string> string_queue;
    string_queue.enqueue("Hello");
    string_queue.enqueue("World");

    // Using constants from nested namespaces
    std::cout << "Speed of light: " << Constants::Physics::SPEED_OF_LIGHT << " m/s" << std::endl;
    std::cout << "Seconds per day: " << (Constants::Time::SECONDS_PER_MINUTE *
                                         Constants::Time::MINUTES_PER_HOUR *
                                         Constants::Time::HOURS_PER_DAY) << std::endl;

    // Using function overloads
    Utils::print(42);
    Utils::print(3.14159);
    Utils::print(std::string("Hello, World!"));

    std::vector<int> numbers = {1, 2, 3, 4, 5};
    Utils::print(numbers);

    // Using extended namespace
    double cube_result = Math::cube(3.0);
    std::cout << "Cube of 3: " << cube_result << std::endl;

    Math::Calculator calc(10.0);
    double result = calc.add(5.0).multiply(2.0).getValue();
    std::cout << "Calculator result: " << result << std::endl;

    // Using inline namespace (v2 is default)
    Version::API::processData();  // Uses v2 by default
    Version::v1::API::processData();  // Explicitly use v1

    // Using geometry namespace
    Geometry::Point p1(1.0, 2.0);
    Geometry::Point p2(3.0, 4.0);
    Geometry::Point p3 = p1 + p2;
    std::cout << "Point addition: " << p3 << std::endl;

    double dist = Geometry::distance(p1, p2);
    std::cout << "Distance between points: " << dist << std::endl;

    // Using database namespace
    if (Database::ConnectionPool::acquireConnection()) {
        std::cout << "Connection acquired. Total: " << Database::ConnectionPool::getCurrentConnections() << std::endl;
        Database::ConnectionPool::releaseConnection();
    }

#ifdef FEATURE_EXPERIMENTAL
    // Using conditional namespace
    Experimental::experimentalFeature();
    Experimental::ExperimentalClass exp;
    exp.test();
#endif

    return 0;
}
