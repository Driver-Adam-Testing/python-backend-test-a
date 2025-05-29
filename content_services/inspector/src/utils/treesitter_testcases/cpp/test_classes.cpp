#include <iostream>
#include <memory>
#include <vector>

// 1. Basic class definition
class BasicClass {
private:
    int value;

public:
    BasicClass(int v) : value(v) {}
    int getValue() const { return value; }
};

// 3. Class with different access levels
class AccessLevels {
private:
    int private_data;

protected:
    int protected_data;

public:
    int public_data;

    AccessLevels() : private_data(1), protected_data(2), public_data(3) {}
};

// 4. Abstract base class with pure virtual functions
class AbstractShape {
public:
    virtual ~AbstractShape() = default;
    virtual double getArea() const = 0;
    virtual double getPerimeter() const = 0;
    virtual void print() const = 0;
};

// 5. Inheritance - single inheritance
class Circle : public AbstractShape {
private:
    double radius;

public:
    Circle(double r) : radius(r) {}

    double getArea() const override {
        return 3.14159 * radius * radius;
    }

    double getPerimeter() const override {
        return 2 * 3.14159 * radius;
    }

    void print() const override {
        std::cout << "Circle with radius " << radius << std::endl;
    }
};

// 6. Multiple inheritance
class Drawable {
public:
    virtual void draw() const = 0;
};

class Serializable {
public:
    virtual std::string serialize() const = 0;
};

class DrawableShape : public AbstractShape, public Drawable, public Serializable {
protected:
    std::string name;

public:
    DrawableShape(const std::string& shape_name) : name(shape_name) {}
    virtual ~DrawableShape() = default;
};

// 7. Diamond inheritance with virtual base
class Animal {
protected:
    std::string species;

public:
    Animal(const std::string& s) : species(s) {}
    virtual void makeSound() const = 0;
};

class Mammal : public virtual Animal {
public:
    Mammal(const std::string& s) : Animal(s) {}
    void nurse() const { std::cout << "Nursing babies" << std::endl; }
};

class Bird : public virtual Animal {
public:
    Bird(const std::string& s) : Animal(s) {}
    void fly() const { std::cout << "Flying" << std::endl; }
};

class Bat : public Mammal, public Bird {
public:
    Bat() : Animal("Bat"), Mammal("Bat"), Bird("Bat") {}

    void makeSound() const override {
        std::cout << "Squeaking" << std::endl;
    }
};

// 8. Template classes
template<typename T>
class Container {
private:
    T data;

public:
    Container(const T& initial_data) : data(initial_data) {}

    T get() const { return data; }
    void set(const T& new_data) { data = new_data; }
};

// 9. Template class with multiple parameters
template<typename KeyType, typename ValueType, int Size = 10>
class FixedMap {
private:
    KeyType keys[Size];
    ValueType values[Size];
    int count;

public:
    FixedMap() : count(0) {}

    void insert(const KeyType& key, const ValueType& value) {
        if (count < Size) {
            keys[count] = key;
            values[count] = value;
            count++;
        }
    }

    ValueType* find(const KeyType& key) {
        for (int i = 0; i < count; i++) {
            if (keys[i] == key) {
                return &values[i];
            }
        }
        return nullptr;
    }
};

// 10. Template specialization
template<>
class Container<bool> {
private:
    bool data;

public:
    Container(bool initial_data) : data(initial_data) {}

    bool get() const { return data; }
    void set(bool new_data) { data = new_data; }
    void flip() { data = !data; }
};

// 11. Nested classes
class Outer {
private:
    int outer_value;

public:
    class Inner {
    private:
        int inner_value;

    public:
        Inner(int val) : inner_value(val) {}
        int getValue() const { return inner_value; }
    };

    struct InnerStruct {
        double x, y;
        InnerStruct(double x_val, double y_val) : x(x_val), y(y_val) {}
    };

    Outer(int val) : outer_value(val) {}
    Inner createInner(int val) const { return Inner(val); }
};

// 12. Friend classes
class FriendClass {
private:
    int secret_data;

public:
    FriendClass(int data) : secret_data(data) {}
    friend class FriendlyClass;
};

class FriendlyClass {
public:
    static void revealSecret(const FriendClass& obj) {
        std::cout << "Secret: " << obj.secret_data << std::endl;
    }
};

// 13. Static members
class Counter {
private:
    static int instance_count;
    int id;

public:
    Counter() : id(++instance_count) {}

    static int getInstanceCount() {
        return instance_count;
    }

    int getId() const { return id; }
};

// Static member definition
int Counter::instance_count = 0;

// 14. Const and mutable members
class ConstExample {
private:
    int immutable_data;
    mutable int cache_value;
    mutable bool cache_valid;

public:
    ConstExample(int data) : immutable_data(data), cache_value(0), cache_valid(false) {}

    int getExpensiveValue() const {
        if (!cache_valid) {
            cache_value = immutable_data * immutable_data;  // Expensive calculation
            cache_valid = true;
        }
        return cache_value;
    }
};

// 15. RAII (Resource Acquisition Is Initialization) class
class FileWrapper {
private:
    FILE* file_handle;

public:
    FileWrapper(const char* filename, const char* mode) {
        file_handle = fopen(filename, mode);
        if (!file_handle) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~FileWrapper() {
        if (file_handle) {
            fclose(file_handle);
        }
    }

    // Delete copy constructor and assignment operator
    FileWrapper(const FileWrapper&) = delete;
    FileWrapper& operator=(const FileWrapper&) = delete;

    // Allow move operations
    FileWrapper(FileWrapper&& other) noexcept : file_handle(other.file_handle) {
        other.file_handle = nullptr;
    }

    FileWrapper& operator=(FileWrapper&& other) noexcept {
        if (this != &other) {
            if (file_handle) {
                fclose(file_handle);
            }
            file_handle = other.file_handle;
            other.file_handle = nullptr;
        }
        return *this;
    }

    FILE* get() const { return file_handle; }
};

// 16. Policy-based design
template<typename PrintPolicy>
class Logger {
private:
    PrintPolicy printer;

public:
    template<typename... Args>
    void log(const Args&... args) {
        printer.print(args...);
    }
};

class ConsolePrinter {
public:
    template<typename... Args>
    void print(const Args&... args) {
        ((std::cout << args << " "), ...);
        std::cout << std::endl;
    }
};

// 17. Singleton pattern
class Singleton {
private:
    static std::unique_ptr<Singleton> instance;
    static std::once_flag initialized;

    Singleton() = default;

public:
    static Singleton& getInstance() {
        std::call_once(initialized, []() {
            instance = std::unique_ptr<Singleton>(new Singleton());
        });
        return *instance;
    }

    // Delete copy constructor and assignment operator
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;

    void doSomething() {
        std::cout << "Singleton doing something" << std::endl;
    }
};

// Static member definitions
std::unique_ptr<Singleton> Singleton::instance = nullptr;
std::once_flag Singleton::initialized;

// 18. Forward declarations
class ForwardDeclared;

class UsesForwardDeclaration {
private:
    ForwardDeclared* ptr;

public:
    UsesForwardDeclaration();
    ~UsesForwardDeclaration();
    void useForwardDeclared();
};

class ForwardDeclared {
public:
    void doSomething() {
        std::cout << "Forward declared class method" << std::endl;
    }
};

// Method definitions for UsesForwardDeclaration
UsesForwardDeclaration::UsesForwardDeclaration() : ptr(new ForwardDeclared()) {}

UsesForwardDeclaration::~UsesForwardDeclaration() {
    delete ptr;
}

void UsesForwardDeclaration::useForwardDeclared() {
    ptr->doSomething();
}

// 20. Anonymous namespace class
namespace {
    class AnonymousNamespaceClass {
    public:
        void doSomething() {
            std::cout << "Anonymous namespace class" << std::endl;
        }
    };
}

int main() {
    BasicClass bc(42);
    Circle circle(5.0);
    Bat bat;

    Container<int> int_container(100);
    Container<bool> bool_container(true);

    Outer outer(10);
    Outer::Inner inner(20);

    Counter c1, c2, c3;
    std::cout << "Total counters created: " << Counter::getInstanceCount() << std::endl;

    Singleton& singleton = Singleton::getInstance();
    singleton.doSomething();

    Logger<ConsolePrinter> logger;
    logger.log("Hello", "World", 123);

    AnonymousNamespaceClass anon;
    anon.doSomething();

    return 0;
}
