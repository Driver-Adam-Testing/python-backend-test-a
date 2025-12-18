# Test file for Ruby function call extraction
# This file contains various patterns of function/method calls in Ruby

# =============================================================================
# Top-level calls
# =============================================================================

puts "Hello, world!"
print "This is a test"
p "Debug output"

# =============================================================================
# Simple function calls
# =============================================================================

result = calculate(1, 2, 3)
value = get_user_data
create_user(name: "John", age: 30)

# =============================================================================
# Class definition with various calls
# =============================================================================

class User
  attr_accessor :name, :age

  def initialize(name, age)
    @name = name
    @age = age
  end

  def save
    validate_data
    user.update
    puts "User saved"
  end

  def save!
    raise "Invalid" unless valid?
    save
  end

  def valid?
    !name.empty? && age > 0
  end

  def self.find(id)
    User.new("Default", 0)
  end

  def self.create(attributes)
    user = User.new(attributes[:name], attributes[:age])
    user.save
    user
  end

  def self.all
    []
  end
end

# =============================================================================
# Instance method calls
# =============================================================================

user = User.new("Alice", 25)
user.save
user.update
user.destroy

# =============================================================================
# Class method calls
# =============================================================================

found_user = User.find(1)
all_users = User.all
new_user = User.create(name: "Bob", age: 30)

# =============================================================================
# Chained method calls
# =============================================================================

title = user.posts.first.title
result = user.team.members.active.count

# =============================================================================
# Calls with blocks (braces)
# =============================================================================

[1, 2, 3].each { |x| puts x }
names = users.map { |u| u.name }
active_users = users.select { |u| u.active? }

# =============================================================================
# Calls with blocks (do...end)
# =============================================================================

File.open("data.txt") do |f|
  content = f.read
  puts content
end

users.each do |user|
  user.save
  user.notify
end

# =============================================================================
# Common iterators
# =============================================================================

results = array.map { |x| x * 2 }
filtered = list.select { |item| item.valid? }
rejected = list.reject { |item| item.invalid? }
sum = numbers.reduce(0) { |acc, n| acc + n }

# =============================================================================
# Super and yield
# =============================================================================

class Admin < User
  def save
    super
    log_admin_action
  end

  def process(&block)
    yield if block_given?
    yield(data) if block_given?
  end
end

# =============================================================================
# Namespaced calls
# =============================================================================

module MyModule
  class MyClass
    def self.some_method
      puts "Called"
    end
  end
end

MyModule::MyClass.some_method

module Outer
  module Middle
    module Inner
      def self.helper
        puts "Nested"
      end
    end
  end
end

Outer::Middle::Inner.helper

# =============================================================================
# Safe navigation operator
# =============================================================================

user_name = user&.name
post_title = user&.posts&.first&.title

# =============================================================================
# Conditional assignment with calls
# =============================================================================

@user ||= User.find(session[:user_id])
@cache ||= initialize_cache

# =============================================================================
# Self calls
# =============================================================================

class UserService
  def process
    self.validate
    sanitize_data
    self.save_to_database
  end

  def validate
    puts "Validating"
  end

  def sanitize_data
    puts "Sanitizing"
  end

  def save_to_database
    puts "Saving"
  end
end

# =============================================================================
# Calls in string interpolation
# =============================================================================

message = "Hello #{user.name}, you are #{user.age} years old"
info = "User count: #{User.count}"

# =============================================================================
# Symbol-to-proc and functional style
# =============================================================================

names = users.map(&:name)
emails = users.map(&:email)

my_proc = proc { |x| x * 2 }
result = my_proc.call(5)

my_lambda = ->(x) { x + 1 }
value = my_lambda.call(10)

# =============================================================================
# Parallel assignment
# =============================================================================

x, y = get_coordinates
first, *rest = get_list

# =============================================================================
# Calls in control structures
# =============================================================================

if user.valid?
  user.save
else
  user.errors
end

while has_more?
  item = queue.pop
  item.process
end

case user.role
when "admin"
  grant_admin_access
when "user"
  grant_user_access
end

# =============================================================================
# Bang and query methods
# =============================================================================

data.compact!
array.uniq!
hash.delete!(:key)

result.nil?
array.empty?
user.persisted?

# =============================================================================
# Singleton class
# =============================================================================

class Configuration
  class << self
    def load
      read_file("config.yml")
      parse_yaml
    end

    def read_file(path)
      File.read(path)
    end

    def parse_yaml
      puts "Parsing"
    end
  end
end

Configuration.load

# =============================================================================
# Module methods
# =============================================================================

module Helper
  def self.format(text)
    text.upcase
  end

  def self.sanitize(data)
    data.strip
  end
end

Helper.format("test")
Helper.sanitize(" data ")

# =============================================================================
# Splat operators
# =============================================================================

def process_all(*args)
  args.each { |arg| puts arg }
end

process(*arguments)
create(**options)

# =============================================================================
# Dynamic calls
# =============================================================================

obj.send(:method_name, arg1, arg2)
obj.public_send(:safe_method)
obj.__send__(:any_method)

# =============================================================================
# Metaprogramming
# =============================================================================

class DynamicClass
  define_method(:dynamic_method) do
    puts "Dynamically created"
  end

  def method_missing(method_name, *args)
    super
  end
end

# =============================================================================
# Eval family
# =============================================================================

eval("puts 'evaluated'")
instance_eval { puts "instance context" }
class_eval { def new_method; end }

# =============================================================================
# Raise and exception handling
# =============================================================================

def risky_operation
  raise StandardError, "Something went wrong"
  fail "This also raises"
end

begin
  risky_operation
rescue => e
  handle_error(e)
ensure
  cleanup
end

# =============================================================================
# Return context
# =============================================================================

def with_return
  return calculate(x) if early_exit?
  process_data
end

# =============================================================================
# Hash and array operations
# =============================================================================

value = hash.fetch(:key, default_value)
item = hash[:key]
data = nested.dig(:level1, :level2, :level3)

# =============================================================================
# Tap and then (uncommon patterns)
# =============================================================================

user = User.new("Test", 20).tap { |u| u.save }
result = value.then { |v| v * 2 }
data = input.yield_self { |i| i.transform }

# =============================================================================
# Calls inside blocks
# =============================================================================

users.each do |u|
  u.save
  u.notify
  send_email(u.email)
end

# =============================================================================
# Modifier if/unless
# =============================================================================

user.save if user.valid?
user.destroy unless user.persisted?

# =============================================================================
# Multiple calls in one line
# =============================================================================

user.save and user.reload or user.create
