// inheritance test cases for base_class_clause functionality

// 1. Simple public inheritance
class Base {};
class PublicDerived : public Base {};

// 2. Simple private inheritance (default for class)
class PrivateDerived : private Base {};

// 3. Simple protected inheritance
class ProtectedDerived : protected Base {};

// 4. Default inheritance (private for class, public for struct)
class DefaultClassDerived : Base {};
struct DefaultStructDerived : Base {};

// 5. Virtual inheritance
class VirtualBase {};
class VirtualDerived : virtual public VirtualBase {};

// 6. Multiple inheritance with different access levels
class BaseA {};
class BaseB {};
class BaseC {};
class MultipleInheritance : public BaseA, private BaseB, protected BaseC {};

// 7. Virtual multiple inheritance (diamond problem solution)
class Animal {};
class Mammal : virtual public Animal {};
class Bird : virtual public Animal {};
class FlyingMammal : public Mammal, public Bird {};

// 8. Template base classes
template<typename T>
class TemplateBase {};

class TemplateInheritance : public TemplateBase<int> {};

// 9. Qualified base class names
namespace NS {
    class NamespacedBase {};
}

class QualifiedInheritance : public NS::NamespacedBase {};

// 10. Nested class inheritance
class Outer {
public:
    class Inner {};
};

class InheritFromNested : public Outer::Inner {};

// 11. Complex template inheritance
template<typename T, int N>
class ComplexTemplate {};

class ComplexTemplateInheritance : public ComplexTemplate<std::string, 42> {};

// 12. Mixed virtual and non-virtual inheritance
class MixedBase1 {};
class MixedBase2 {};
class MixedInheritance : virtual public MixedBase1, private MixedBase2 {};

// 13. Inheritance with very long base class lists
class LongBase1 {};
class LongBase2 {};
class LongBase3 {};
class LongBase4 {};
class LongBase5 {};
class VeryLongInheritance : public LongBase1, 
                           protected LongBase2, 
                           private LongBase3,
                           virtual public LongBase4,
                           virtual protected LongBase5 {};

// 14. Struct inheritance (should default to public)
struct StructBase {};
struct StructDerived : StructBase {};
struct StructExplicitPrivate : private StructBase {};

// 15. Abstract base with multiple derived classes
class AbstractBase {
public:
    virtual ~AbstractBase() = default;
    virtual void pure_virtual() = 0;
};

class ConcreteA : public AbstractBase {
public:
    void pure_virtual() override {}
};

class ConcreteB : public AbstractBase {
public:
    void pure_virtual() override {}
};

// 16. Deep inheritance hierarchy
class Level1 {};
class Level2 : public Level1 {};
class Level3 : public Level2 {};
class Level4 : public Level3 {};

// 17. Inheritance with forward declared base
class ForwardDeclaredBase;
class ForwardInheritance : public ForwardDeclaredBase {};

// Definition after inheritance
class ForwardDeclaredBase {
public:
    virtual ~ForwardDeclaredBase() = default;
};

// 18. Template class inheriting from template
template<typename T>
class TemplateBaseClass {};

template<typename U>
class TemplateDerived : public TemplateBaseClass<U> {};

// 19. Specialization inheritance
template<>
class TemplateDerived<bool> : public TemplateBaseClass<int> {};

// 20. Anonymous namespace inheritance
namespace {
    class AnonymousBase {};
}

class InheritFromAnonymous : public AnonymousBase {};