// C++ union test cases - focusing on C++ specific features not available in C

#include <string>
#include <new>

// Basic union with constructors and destructor (C++ feature)
union BasicUnion {
    int int_value;
    double double_value;
    
    BasicUnion() : int_value(0) {}
    BasicUnion(int v) : int_value(v) {}
    BasicUnion(double v) : double_value(v) {}
    ~BasicUnion() {}
};

// Union with member functions (C++ feature)
union FunctionUnion {
    int i;
    float f;
    
    FunctionUnion() : i(0) {}
    
    void setInt(int value) {
        i = value;
    }
    
    void setFloat(float value) {
        f = value;
    }
    
    int getInt() const { return i; }
    float getFloat() const { return f; }
};

// Union with non-trivial types (C++11 feature)
union ComplexUnion {
    int simple_int;
    std::string complex_string;
    
    ComplexUnion() : simple_int(0) {}
    
    ComplexUnion(int i) : simple_int(i) {}
    
    ComplexUnion(const std::string& s) {
        new(&complex_string) std::string(s);
    }
    
    ~ComplexUnion() {
        // Note: Need to manually handle destruction
    }
};

// Anonymous union (C++ scoping)
namespace {
    union {
        int global_int;
        double global_double;
    } anonymous_global_union;
}

// Union inside namespace (C++ scoping)
namespace UnionNamespace {
    union NamespacedUnion {
        int value;
        char bytes[4];
        
        NamespacedUnion() : value(0) {}
        NamespacedUnion(int v) : value(v) {}
    };
    
    namespace Inner {
        union DeeplyNested {
            long long_val;
            double double_val;
            
            DeeplyNested() : long_val(0) {}
        };
    }
}

// Union inside class (C++ feature)
class ContainerClass {
public:
    union PublicUnion {
        int int_member;
        float float_member;
        
        PublicUnion() : int_member(0) {}
        void setInt(int v) { int_member = v; }
    };
    
private:
    union PrivateUnion {
        short short_val;
        char char_array[2];
        
        PrivateUnion() : short_val(0) {}
    };
    
    PrivateUnion private_union_member;
    
public:
    ContainerClass() {}
};

// Tagged union pattern (C++ implementation)
struct TaggedUnion {
    enum Type { INT, DOUBLE, STRING } type;
    
    union {
        int int_value;
        double double_value;
        std::string string_value;
    };
    
    TaggedUnion() : type(INT), int_value(0) {}
    
    TaggedUnion(int v) : type(INT), int_value(v) {}
    
    TaggedUnion(double v) : type(DOUBLE), double_value(v) {}
    
    TaggedUnion(const std::string& s) : type(STRING) {
        new(&string_value) std::string(s);
    }
    
    ~TaggedUnion() {
        if (type == STRING) {
            string_value.~string();
        }
    }
};

// Template with union (C++ feature)
template<typename T, typename U>
struct TemplateUnionContainer {
    union {
        T first_type;
        U second_type;
    };
    
    bool is_first;
    
    TemplateUnionContainer() : first_type{}, is_first(true) {}
    
    void setFirst(const T& value) {
        if (!is_first) {
            second_type.~U();
        }
        new(&first_type) T(value);
        is_first = true;
    }
    
    void setSecond(const U& value) {
        if (is_first) {
            first_type.~T();
        }
        new(&second_type) U(value);
        is_first = false;
    }
};

// Union with static members (C++ feature)
union StaticUnion {
    int int_val;
    double double_val;
    
    static int usage_counter;
    
    StaticUnion() : int_val(0) {
        ++usage_counter;
    }
    
    static int getUsageCount() {
        return usage_counter;
    }
};
int StaticUnion::usage_counter = 0;

int main() {
    BasicUnion bu(42);
    FunctionUnion fu;
    fu.setInt(10);
    
    UnionNamespace::NamespacedUnion nu(5);
    ContainerClass::PublicUnion pu;
    
    TaggedUnion tu("hello");
    TemplateUnionContainer<int, double> tuc;
    
    StaticUnion su;
    
    return 0;
}
