# Test file for Ruby attribute extraction
# Tests attr_accessor, attr_reader, attr_writer

# Simple class with basic attributes
class SimpleAttributes
  attr_accessor :name, :age
  attr_reader :id
  attr_writer :status
end

# Class with single attribute declarations
class SingleAttributes
  attr_accessor :username
  attr_reader :created_at
  attr_writer :password
end

# Class with mixed attributes
class MixedAttributes
  attr_accessor :first_name, :last_name
  attr_reader :email, :phone
  attr_writer :address, :city, :zip

  def initialize
    @internal_var = "not an attribute"
  end
end

# Module with attributes
module AttributeModule
  attr_accessor :config
  attr_reader :version
  attr_writer :debug_mode
end

# Nested classes with attributes
class OuterAttributes
  attr_accessor :outer_attr

  class InnerAttributes
    attr_accessor :inner_attr
    attr_reader :inner_readonly
  end
end

# Class with attributes and constants
class AttributesWithConstants
  CONSTANT = 100

  attr_accessor :name
  attr_reader :id
end

# Class with attributes in different positions
class AttributesInDifferentPositions
  attr_accessor :first

  def some_method
    # Method in between
  end

  attr_reader :second

  def another_method
    # Another method
  end

  attr_writer :third
end

# Class with symbol variations
class SymbolVariations
  attr_accessor :simple_symbol
  attr_reader :"symbol_with_quotes"
  attr_writer :symbol_with_underscore_and_numbers_123
end

# Empty class (no attributes)
class NoAttributes
  def initialize
    @var = 1
  end
end

# Class with only attr_accessor
class OnlyAccessor
  attr_accessor :read_write_1, :read_write_2
end

# Class with only attr_reader
class OnlyReader
  attr_reader :readonly_1, :readonly_2, :readonly_3
end

# Class with only attr_writer
class OnlyWriter
  attr_writer :writeonly_1
end

# Class with duplicate attribute names (unusual but technically valid)
class DuplicateAttributes
  attr_accessor :name
  attr_reader :name  # Overwrites accessor's reader with just reader
end

# Class with attributes using different quote styles
class QuoteStyles
  attr_accessor :single, :"double"
  attr_reader :no_quotes
end

# Module nested in class
class ClassWithAttributeModule
  attr_accessor :class_attr

  module NestedAttributeModule
    attr_accessor :nested_attr
    attr_reader :nested_readonly
  end
end

# Class with attributes and visibility modifiers
class AttributesWithVisibility
  attr_accessor :public_attr

  private

  attr_accessor :private_attr  # Note: attr_accessor creates public methods even after private

  def private_method
    # private method
  end
end

# Class with multiple attributes on same line with trailing comma
class TrailingComma
  attr_accessor :attr1, :attr2,
end

# Class reopening with attributes
class ReopenedAttributeClass
  attr_accessor :first
end

class ReopenedAttributeClass
  attr_reader :second
end

# Singleton class with attributes
class SingletonAttributes
  attr_accessor :class_attr

  class << self
    attr_accessor :singleton_attr
  end
end

# Class with attributes using percent notation (rare)
# class PercentNotation
#   attr_accessor :%w[attr1 attr2]  # This doesn't work in Ruby, commented out
# end

# Class with attributes that look like method calls
class AttributesLikeMethodCalls
  attr_accessor(:method_style_1, :method_style_2)
  attr_reader :mixed, :style
end

# Multiple attributes with various access patterns
class ComplexAccessPatterns
  attr_accessor :full_access
  attr_reader :read_only
  attr_writer :write_only

  # Same attribute declared multiple times (last wins)
  attr_accessor :changing
  attr_reader :changing  # Now read-only
  attr_writer :changing  # Now write-only
end

# Unicode in attribute names
class UnicodeAttributes
  attr_accessor :café
  attr_reader :naïve
end

# Numbers in attribute names
class NumberAttributes
  attr_accessor :attr_1, :attr_2
  attr_reader :readonly_3
end

# Class with no body statements except attributes
class OnlyAttributesNoMethods
  attr_accessor :a
  attr_reader :b
  attr_writer :c
end
