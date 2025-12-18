# Test file for Ruby callable extraction

# Top-level methods (no class or module)
def top_level_method
  "I'm at the top level"
end

def another_top_level
  42
end

# Class with instance methods
class MyClass
  def instance_method_one
    "one"
  end

  def instance_method_two
    "two"
  end
end

# Class with class methods (singleton methods)
class ClassWithClassMethods
  def self.class_method_one
    "class one"
  end

  def self.class_method_two
    "class two"
  end
end

# Class with mixed instance and class methods
class Calculator
  def add(a, b)
    a + b
  end

  def self.version
    "1.0"
  end

  def subtract(a, b)
    a - b
  end

  def self.author
    "John Doe"
  end
end

# Class with visibility modifiers - private keyword
class WithPrivateKeyword
  def public_method
    "public"
  end

  private

  def private_method_one
    "private one"
  end

  def private_method_two
    "private two"
  end
end

# Class with visibility modifiers - protected keyword
class WithProtectedKeyword
  def public_method
    "public"
  end

  protected

  def protected_method
    "protected"
  end
end

# Class with explicit public keyword
class WithExplicitPublic
  private

  def private_method
    "private"
  end

  public

  def explicitly_public_method
    "public"
  end
end

# Class with inline visibility modifiers
class WithInlineVisibility
  private def inline_private
    "private"
  end

  protected def inline_protected
    "protected"
  end

  public def inline_public
    "public"
  end
end

# Nested classes in modules
module MyModule
  class OuterClass
    def outer_method
      "outer"
    end

    class InnerClass
      def inner_method
        "inner"
      end
    end
  end
end

# Mixed contexts - top-level, class, and nested
def top_level_helper
  "helper"
end

class FirstClass
  def first_instance
    "first"
  end

  def self.first_class_method
    "class"
  end
end

module AnotherModule
  class SecondClass
    def second_instance
      "second"
    end
  end
end

def another_helper
  "another"
end

# Empty class
class EmptyClass
end

# Class with only private methods
class OnlyPrivate
  private

  def secret_one
    "secret"
  end

  def secret_two
    "another secret"
  end
end

# Class with multiple visibility changes
class VisibilityChanges
  def starts_public
    "public"
  end

  private

  def goes_private
    "private"
  end

  protected

  def then_protected
    "protected"
  end

  public

  def back_to_public
    "public again"
  end

  private

  def ends_private
    "private again"
  end
end

# Module with methods
module Utilities
  def utility_method
    "utility"
  end

  def self.module_method
    "module level"
  end
end

# Class with various parameter patterns
class ParameterTest
  def no_params
  end

  def single_param(a)
  end

  def multiple_params(a, b, c)
  end

  def default_params(a = 1, b = 2)
  end

  def keyword_params(name:, age:)
  end

  def splat_params(*args)
  end

  def block_param(&block)
  end
end
