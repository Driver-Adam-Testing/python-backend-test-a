# Test file for Ruby class and module extraction

# Simple class with instance and class methods (for backward compatibility)
class Calculator
  # Instance method - operates on an instance
  def add(a, b)
    a + b
  end

  # Class method - called on the class itself
  def self.subtract(a, b)
    a - b
  end
end

# Class with inheritance
class Animal
end

class Dog < Animal
end

# Class with single include
module Walkable
end

class Person
  include Walkable
end

# Class with multiple includes in one statement
module Swimmable
end

module Runnable
end

class Athlete
  include Walkable, Swimmable, Runnable
end

# Class with multiple include statements (should deduplicate)
class MultiInclude
  include Walkable
  include Swimmable
  include Walkable  # duplicate - should be removed
end

# Class with single extend
module ClassMethods
end

class WithExtend
  extend ClassMethods
end

# Class with multiple extends
module Loggable
end

module Configurable
end

class Service
  extend Loggable, Configurable
end

# Class with both include and extend
module InstanceMethods
end

module MoreClassMethods
end

class FullFeatured
  include InstanceMethods
  extend MoreClassMethods
end

# Class with inheritance, include, and extend
class BaseClass
end

module Mixin1
end

module Mixin2
end

class CompleteClass < BaseClass
  include Mixin1
  extend Mixin2
end

# Module definition
module MyModule
  def module_method
    "method"
  end
end

# Module with include
module ComposedModule
  include Walkable
end

# Module with extend
module ExtendedModule
  extend ClassMethods
end

# Module with both
module FullModule
  include Mixin1
  extend Mixin2
end

# Nested class
class Outer
  class Inner
  end
end

# Nested module
module OuterModule
  module InnerModule
  end
end

# Class inside module
module Namespace
  class NamespacedClass
  end
end

# Module inside class (less common but valid)
class Container
  module NestedModule
  end
end

# Class with namespaced include/extend
module ActiveSupport
  module Concern
  end
end

class WithNamespacedMixins
  include ActiveSupport::Concern
end

# Empty class
class Empty
end

# Empty module
module EmptyModule
end

# Class with complex inheritance chain
class Level1
end

class Level2 < Level1
end

class Level3 < Level2
end

# Class with single prepend
module Prependable
end

class PrependSingle
  prepend Prependable
end

# Class with multiple prepends in one statement
module PrependA
end

module PrependB
end

class PrependMultiple
  prepend PrependA, PrependB
end

# Class with multiple prepend statements (should deduplicate)
class PrependDeduplicate
  prepend PrependA
  prepend PrependB
  prepend PrependA  # duplicate - should be removed
end

# Class with include, extend, and prepend
class MixedMixins
  include Walkable
  extend ClassMethods
  prepend Prependable
end

# Module with prepend
module ModuleWithPrepend
  prepend PrependA
end

# Nested class with prepend
class OuterPrepend
  prepend PrependA

  class InnerPrepend
    prepend PrependB
  end
end

# Class with namespaced prepend
module Namespaced
  module PrependModule
  end
end

class NamespacedPrepend
  prepend Namespaced::PrependModule
end
