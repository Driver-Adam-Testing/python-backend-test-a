// C++ struct test cases - focusing on C++ specific features not available in C

#include <memory>
#include <string>

// Basic struct with constructors (C++ feature)
struct BasicStruct {
    int value;

    BasicStruct() : value(0) {}
    BasicStruct(int v) : value(v) {}
    ~BasicStruct() {}

    void setValue(int v) { value = v; }
    int getValue() const { return value; }
};

// Struct with access specifiers (C++ feature)
struct AccessStruct {
public:
    int public_value;
    AccessStruct() : public_value(0), private_value(0) {}

private:
    int private_value;
    void privateMethod() {}

protected:
    void protectedMethod() {}
};

// Struct with inheritance (C++ feature)
struct BaseStruct {
    int base_value;
    BaseStruct(int v) : base_value(v) {}
    virtual ~BaseStruct() = default;
    virtual void virtualMethod() = 0;
};

struct DerivedStruct : public BaseStruct {
    int derived_value;
    DerivedStruct(int b, int d) : BaseStruct(b), derived_value(d) {}
    void virtualMethod() override {}
};

// Template struct (C++ feature)
template<typename T>
struct TemplateStruct {
    T data;

    TemplateStruct() {}
    TemplateStruct(const T& value) : data(value) {}

    void set(const T& value) { data = value; }
    const T& get() const { return data; }
};

// Struct inside namespace (C++ scoping)
namespace StructNamespace {
    struct NamespacedStruct {
        int value;
        NamespacedStruct(int v) : value(v) {}
    };

    namespace NestedNamespace {
        struct DeeplyNested {
            double data;
            DeeplyNested(double d) : data(d) {}
        };
    };
}

// Struct inside class (C++ feature)
class ContainerClass {
public:
    struct InnerStruct {
        int inner_value;
        InnerStruct(int v) : inner_value(v) {}
        void method() {}
    };

private:
    struct PrivateStruct {
        int secret;
        PrivateStruct(int s) : secret(s) {}
    };
};

// Forward declared struct in C++ context
struct ForwardDeclared;

struct UsesForward {
    ForwardDeclared* ptr;
    UsesForward() : ptr(nullptr) {}
};

struct ForwardDeclared {
    int data;
    ForwardDeclared(int d) : data(d) {}
};

// Anonymous struct in namespace (C++ feature)
namespace {
    struct AnonymousNamespaceStruct {
        int value;
        AnonymousNamespaceStruct() : value(42) {}
    };
}

// Struct with static members (C++ feature)
struct StaticStruct {
    static int counter;
    static const int CONSTANT = 100;

    int instance_value;

    StaticStruct() : instance_value(++counter) {}
    static int getCounter() { return counter; }
};
int StaticStruct::counter = 0;

// Aggregate struct for C++11 aggregate initialization
struct AggregateStruct {
    int a;
    double b;
    bool c;
};

// Struct with deleted/defaulted functions (C++11 feature)
struct ModernStruct {
    int value;

    ModernStruct() = default;
    ModernStruct(int v) : value(v) {}
    ModernStruct(const ModernStruct&) = delete;
    ModernStruct& operator=(const ModernStruct&) = delete;
    ~ModernStruct() = default;
};

int main() {
    BasicStruct bs(10);
    DerivedStruct ds(1, 2);
    TemplateStruct<int> ts(42);
    StructNamespace::NamespacedStruct ns(5);
    ContainerClass::InnerStruct is(7);
    StaticStruct ss;
    AggregateStruct as{1, 2.5, true};
    return 0;
}
