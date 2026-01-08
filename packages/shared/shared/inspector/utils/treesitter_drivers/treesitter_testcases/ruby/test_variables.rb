# Test file for Ruby variable extraction
# Tests constants, instance variables, class variables, and global variables

# Top-level constants
TOP_LEVEL_CONSTANT = 100
ANOTHER_TOP_LEVEL = "string"

# Top-level global variables
$global_config = {}
$global_counter = 0

# Top-level instance variable (rare but valid)
@top_level_instance_var = "top"

# Simple class with various variable types
class SimpleClass
  # Class-level constant
  MAX_SIZE = 1000

  # Class variable
  @@class_counter = 0

  # Instance variables in constructor
  def initialize(name, age)
    @name = name
    @age = age
    @created_at = Time.now
  end

  # Instance variable in another method
  def set_status
    @status = "active"
  end

  # Multiple assignments to same instance variable (should deduplicate)
  def update_name(new_name)
    @name = new_name  # Same @name from initialize
  end

  # Class method modifying class variable
  def self.increment
    @@class_counter += 1
  end

  # Method with local variables (should NOT extract these)
  def process
    local_var = "local"  # Don't extract
    temp = 123           # Don't extract
    @result = local_var  # DO extract @result
  end
end

# Module with constants and instance variables
module MyModule
  # Module constant
  VERSION = "1.0.0"
  CONFIG_KEY = :production

  # Module instance variable (rare, belongs to module object)
  @module_instance_var = []

  def self.setup
    @module_instance_var << "initialized"
  end

  def instance_method
    @instance_var_in_module = "value"
  end
end

# Nested classes with variables
class OuterClass
  OUTER_CONSTANT = "outer"
  @@outer_class_var = 0

  def initialize
    @outer_instance = "outer"
  end

  class InnerClass
    INNER_CONSTANT = "inner"
    @@inner_class_var = 0

    def initialize
      @inner_instance = "inner"
    end

    # Nested class accessing its own variables
    def update
      @inner_instance = "updated"
      @another_inner = "new"
    end
  end
end

# Class with namespaced constant
class NamespacedConstants
  # Simple constant
  SIMPLE = 1

  # Constant assigned to another constant
  REFERENCE = SIMPLE

  # Array constant
  VALID_STATES = ["active", "inactive", "pending"]

  # Hash constant
  CONFIG = { timeout: 30, retries: 3 }
end

# Class with instance variables in various methods
class VariableSpread
  def initialize
    @id = nil
  end

  def method_a
    @var_a = 1
  end

  def method_b
    @var_b = 2
  end

  def method_c
    @var_c = 3
    @var_a = 10  # Duplicate of @var_a from method_a
  end
end

# Multiple instance variables on same line (via parallel assignment)
class ParallelAssignment
  def initialize
    @x, @y = 0, 0
    @width, @height = 100, 200
  end
end

# Global variables defined in different contexts
def some_function
  $global_in_function = "global"  # Global, even though in function
end

class ClassWithGlobal
  def method_with_global
    $global_in_class_method = "also global"
  end
end

# Constants defined in odd places
class ConstantInMethod
  def setup
    # This is technically allowed but triggers warnings in Ruby
    # CONSTANT_IN_METHOD = 100
  end
end

# Class with only constants (no instance variables)
class OnlyConstants
  VERSION = "2.0"
  API_KEY = "secret"
end

# Class with only class variables
class OnlyClassVariables
  @@shared_state = {}
  @@counter = 0
end

# Class with only instance variables (all in methods)
class OnlyInstanceVariables
  def initialize
    @a = 1
    @b = 2
  end

  def setup
    @c = 3
  end
end

# Empty class (no variables)
class EmptyClass
end

# Module nested in class
class ClassWithNestedModule
  OUTER = "outer"

  module NestedModule
    NESTED = "nested"

    def module_method
      @module_var = "value"
    end
  end
end

# Class variables with similar names
class SimilarNames
  @@count = 0
  @@counter = 1
  @@count_total = 2

  def initialize
    @name = "first"
    @name_full = "first last"
    @nickname = "nick"
  end
end

# Unicode and special characters in variable names (valid in Ruby)
class UnicodeVariables
  CAFÉ = "coffee"  # Unicode in constant

  def initialize
    @naïve = true  # Unicode in instance variable
  end
end

# Constants with different value types
class ConstantTypes
  NIL_CONSTANT = nil
  BOOL_TRUE = true
  BOOL_FALSE = false
  INTEGER = 42
  FLOAT = 3.14
  STRING = "text"
  SYMBOL = :symbol
  ARRAY = [1, 2, 3]
  HASH = { key: "value" }
  RANGE = (1..10)
  REGEX = /pattern/
  PROC = -> { puts "lambda" }
end

# Class reopening (Ruby allows this)
class ReopenedClass
  FIRST_CONSTANT = 1

  def initialize
    @first_var = "first"
  end
end

class ReopenedClass  # Same class, adding more
  SECOND_CONSTANT = 2

  def add_var
    @second_var = "second"
  end
end

# Singleton class (class << self)
class SingletonExample
  CLASS_CONSTANT = "class"

  class << self
    # This is actually a class instance variable of the singleton class
    @singleton_var = "singleton"

    def singleton_method
      @another_singleton = "value"
    end
  end

  def instance_method
    @instance = "instance"
  end
end
