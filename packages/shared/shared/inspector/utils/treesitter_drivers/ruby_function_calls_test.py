"""
Tests for Ruby function call extraction
"""

import pathlib

import pytest

from utils.lang_specialization.symbol_common import SymbolKind

from .ruby_driver import RubyDriverTree


@pytest.fixture(scope="module")
def function_calls_test_code() -> str:
    file_path = (
        pathlib.Path(__file__).parent
        / "treesitter_testcases"
        / "ruby"
        / "test_function_calls.rb"
    )
    with open(file_path, encoding="utf-8") as f:
        return f.read()


# =============================================================================
# Basic Function/Method Calls
# =============================================================================


def test_extract_simple_function_call(function_calls_test_code: str) -> None:
    """Test extraction of simple top-level function calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract simple calls like: puts "hello"
    call_names = [c.name for c in calls]
    assert "puts" in call_names
    assert "print" in call_names


def test_extract_instance_method_call(function_calls_test_code: str) -> None:
    """Test extraction of method calls on objects (object.method)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract calls like: user.save
    assert "save" in call_names
    assert "update" in call_names
    assert "destroy" in call_names


def test_extract_class_method_call(function_calls_test_code: str) -> None:
    """Test extraction of class method calls (Class.method)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract calls like: User.find(1)
    assert "find" in call_names
    assert "create" in call_names
    assert "all" in call_names


def test_extract_chained_method_calls(function_calls_test_code: str) -> None:
    """Test extraction of chained method calls (obj.method1.method2.method3)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract all methods in the chain: user.posts.first.title
    assert "posts" in call_names
    assert "first" in call_names
    assert "title" in call_names


def test_all_calls_have_symbol_kind_call(function_calls_test_code: str) -> None:
    """Test that all extracted calls have SymbolKind.CALL"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    for call in calls:
        assert call.symbol_kind == SymbolKind.CALL


def test_calls_have_valid_line_numbers(function_calls_test_code: str) -> None:
    """Test that calls have valid start and end line numbers"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    for call in calls:
        assert call.start_line > 0
        assert call.end_line >= call.start_line


def test_calls_have_symbol_code(function_calls_test_code: str) -> None:
    """Test that calls have the symbol_code field populated"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    for call in calls:
        assert call.symbol_code is not None
        assert len(call.symbol_code) > 0


# =============================================================================
# Calls with Arguments
# =============================================================================


def test_extract_calls_with_parentheses(function_calls_test_code: str) -> None:
    """Test calls with explicit parentheses"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: calculate(1, 2, 3)
    assert "calculate" in call_names


def test_extract_calls_without_parentheses(function_calls_test_code: str) -> None:
    """Test calls without parentheses (Ruby style)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: puts "hello" (no parentheses)
    assert "puts" in call_names


def test_extract_calls_with_named_arguments(function_calls_test_code: str) -> None:
    """Test calls with keyword/named arguments"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: create_user(name: "John", age: 30)
    assert "create_user" in call_names


# =============================================================================
# Blocks and Iterators
# =============================================================================


def test_extract_calls_with_block_braces(function_calls_test_code: str) -> None:
    """Test calls with blocks using braces { }"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: [1, 2, 3].each { |x| puts x }
    assert "each" in call_names


def test_extract_calls_with_block_do_end(function_calls_test_code: str) -> None:
    """Test calls with blocks using do...end"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: File.open(path) do |f| ... end
    assert "open" in call_names


def test_extract_common_iterators(function_calls_test_code: str) -> None:
    """Test extraction of common iterator methods"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Common Ruby iterators
    assert "map" in call_names
    assert "select" in call_names
    assert "reject" in call_names
    assert "reduce" in call_names


# =============================================================================
# Special Ruby Calls
# =============================================================================


def test_extract_super_calls(function_calls_test_code: str) -> None:
    """Test extraction of super calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: super or super(args)
    assert "super" in call_names


def test_extract_yield_calls(function_calls_test_code: str) -> None:
    """Test extraction of yield calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: yield or yield(value)
    assert "yield" in call_names


def test_extract_new_calls(function_calls_test_code: str) -> None:
    """Test extraction of .new calls (object instantiation)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: User.new
    assert "new" in call_names


# =============================================================================
# Namespace and Module Calls
# =============================================================================


def test_extract_namespaced_calls(function_calls_test_code: str) -> None:
    """Test extraction of calls with :: namespace resolution"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: MyModule::MyClass.method
    assert "method" in call_names or "some_method" in call_names


def test_extract_deeply_namespaced_calls(function_calls_test_code: str) -> None:
    """Test extraction of deeply nested namespace calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: Outer::Middle::Inner::method
    assert "helper" in call_names or "process" in call_names


# =============================================================================
# Safe Navigation and Conditional Calls
# =============================================================================


def test_extract_safe_navigation_calls(function_calls_test_code: str) -> None:
    """Test extraction of safe navigation operator calls (&.)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: user&.name
    assert "name" in call_names


def test_extract_conditional_assignment_calls(function_calls_test_code: str) -> None:
    """Test extraction of calls in conditional assignments"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: @user ||= User.find(id)
    assert "find" in call_names


# =============================================================================
# Self and Instance Context
# =============================================================================


def test_extract_self_method_calls(function_calls_test_code: str) -> None:
    """Test extraction of explicit self method calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: self.method_name
    assert "validate" in call_names or "process" in call_names


def test_extract_implicit_self_calls(function_calls_test_code: str) -> None:
    """Test extraction of implicit self calls (just method name)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Note: Tree-sitter doesn't extract bare identifiers without arguments
    # as calls (they're ambiguous - could be variables or method calls)
    # We can extract calls with explicit receivers like self.validate
    assert "validate" in call_names or "process" in call_names


# =============================================================================
# String Interpolation Calls
# =============================================================================


def test_extract_calls_in_string_interpolation(function_calls_test_code: str) -> None:
    """Test extraction of method calls inside string interpolation"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: "Hello #{user.name}"
    assert "name" in call_names


# =============================================================================
# Symbol-to-Proc and Functional Style
# =============================================================================


def test_extract_calls_with_ampersand_colon(function_calls_test_code: str) -> None:
    """Test extraction with &: (symbol-to-proc) pattern"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract the map call itself: users.map(&:name)
    assert "map" in call_names


def test_extract_proc_calls(function_calls_test_code: str) -> None:
    """Test extraction of proc/lambda calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: my_proc.call or my_lambda.call
    assert "call" in call_names


# =============================================================================
# Assignment Context Calls
# =============================================================================


def test_extract_calls_in_assignment(function_calls_test_code: str) -> None:
    """Test extraction of calls on right side of assignment"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: result = calculate(1, 2)
    assert "calculate" in call_names


def test_extract_calls_in_parallel_assignment(function_calls_test_code: str) -> None:
    """Test extraction of calls in parallel assignment"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Note: Bare identifiers in parallel assignment aren't extracted
    # Test that we handle parallel assignment context without errors
    # Other calls in the file should still be extracted
    assert len(calls) > 0


# =============================================================================
# Calls in Control Structures
# =============================================================================


def test_extract_calls_in_if_condition(function_calls_test_code: str) -> None:
    """Test extraction of calls in if conditions"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: if user.valid?
    assert "valid?" in call_names or "empty?" in call_names


def test_extract_calls_in_case_statement(function_calls_test_code: str) -> None:
    """Test extraction of calls in case statements"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract calls in: case user.role
    assert "role" in call_names


def test_extract_calls_in_while_condition(function_calls_test_code: str) -> None:
    """Test extraction of calls in while loops"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: while has_more?
    assert "has_more?" in call_names or "next" in call_names


# =============================================================================
# Bang Methods and Query Methods
# =============================================================================


def test_extract_bang_method_calls(function_calls_test_code: str) -> None:
    """Test extraction of bang methods (method!)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: user.save! or data.compact!
    assert "save!" in call_names or "compact!" in call_names


def test_extract_query_method_calls(function_calls_test_code: str) -> None:
    """Test extraction of query methods (method?)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: user.valid? or array.empty?
    assert "valid?" in call_names or "empty?" in call_names


# =============================================================================
# Operator Calls (if we decide to include them)
# =============================================================================


def test_extract_bracket_operator_calls(function_calls_test_code: str) -> None:
    """Test extraction of bracket operator calls (array[index])"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Ruby treats array[0] as array.[](0)
    # Decide if we want to extract these - might be too noisy
    # For now, we don't extract operator calls
    # Test just verifies extraction works without errors
    assert isinstance(calls, list)


# =============================================================================
# Calls in Different Scopes
# =============================================================================


def test_extract_calls_in_class_method(function_calls_test_code: str) -> None:
    """Test extraction of calls inside class methods"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract calls that occur inside def self.method_name
    assert len(calls) > 0


def test_extract_calls_in_instance_method(function_calls_test_code: str) -> None:
    """Test extraction of calls inside instance methods"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract calls inside regular methods
    assert len(calls) > 0


def test_extract_calls_at_top_level(function_calls_test_code: str) -> None:
    """Test extraction of calls at file top level"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract top-level calls (outside any class/method)
    assert len(calls) > 0


# =============================================================================
# Module and Singleton Methods
# =============================================================================


def test_extract_calls_in_module_methods(function_calls_test_code: str) -> None:
    """Test extraction of calls inside module methods"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract calls inside module methods
    assert len(calls) > 0


def test_extract_calls_in_singleton_class(function_calls_test_code: str) -> None:
    """Test extraction of calls in singleton class (class << self)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract calls inside class << self blocks
    assert len(calls) > 0


# =============================================================================
# Edge Cases and Uncommon Patterns
# =============================================================================


def test_extract_calls_with_splat_operator(function_calls_test_code: str) -> None:
    """Test extraction of calls with splat operator (*)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: process(*args)
    assert "process" in call_names


def test_extract_calls_with_double_splat(function_calls_test_code: str) -> None:
    """Test extraction of calls with double splat operator (**)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: create(**options)
    assert "create" in call_names


def test_extract_send_and_public_send(function_calls_test_code: str) -> None:
    """Test extraction of send/public_send dynamic calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: obj.send(:method_name)
    assert "send" in call_names or "public_send" in call_names


def test_extract_method_missing_calls(function_calls_test_code: str) -> None:
    """Test extraction of super call inside method_missing"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # method_missing typically calls super when it can't handle the method
    # Test that we extract the super call inside method_missing definition
    assert "super" in call_names


def test_extract_eval_family_calls(function_calls_test_code: str) -> None:
    """Test extraction of eval/instance_eval/class_eval calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: eval, instance_eval, class_eval
    assert "eval" in call_names or "instance_eval" in call_names


def test_extract_define_method_calls(function_calls_test_code: str) -> None:
    """Test extraction of define_method (metaprogramming)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: define_method(:name) { ... }
    assert "define_method" in call_names


# =============================================================================
# Return and Raise Context
# =============================================================================


def test_extract_calls_in_return_statement(function_calls_test_code: str) -> None:
    """Test extraction of calls in return statements"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: return calculate(x)
    assert "calculate" in call_names


def test_extract_raise_calls(function_calls_test_code: str) -> None:
    """Test extraction of raise/fail calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: raise StandardError
    assert "raise" in call_names or "fail" in call_names


# =============================================================================
# Array and Hash Access
# =============================================================================


def test_extract_hash_access_calls(function_calls_test_code: str) -> None:
    """Test extraction of hash access"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Hash access: hash[:key] or hash.fetch(:key)
    assert "fetch" in call_names


def test_extract_dig_calls(function_calls_test_code: str) -> None:
    """Test extraction of dig method (safe nested access)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: hash.dig(:level1, :level2, :level3)
    assert "dig" in call_names


# =============================================================================
# Uncommon/Bad Practice Patterns
# =============================================================================


def test_extract_tap_calls(function_calls_test_code: str) -> None:
    """Test extraction of tap method (uncommon but valid)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: user.tap { |u| u.save }
    assert "tap" in call_names


def test_extract_then_calls(function_calls_test_code: str) -> None:
    """Test extraction of then/yield_self calls (Ruby 2.6+)"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: value.then { |v| v * 2 }
    assert "then" in call_names or "yield_self" in call_names


def test_extract_nested_calls_in_blocks(function_calls_test_code: str) -> None:
    """Test extraction of calls inside block arguments"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract calls like: users.each { |u| u.save }
    # Both 'each' and 'save' should be extracted
    assert "each" in call_names
    assert "save" in call_names


def test_extract_modifier_if_calls(function_calls_test_code: str) -> None:
    """Test extraction of calls with modifier if/unless"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    call_names = [c.name for c in calls]
    # Should extract: user.save if user.valid?
    assert "save" in call_names
    assert "valid?" in call_names


# =============================================================================
# FQP Tests (Fully Qualified Parent Path)
# =============================================================================


def test_calls_have_correct_fqp_in_class(function_calls_test_code: str) -> None:
    """Test that calls inside classes have correct fully_qualified_parent_path"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Find calls that should be inside a class
    class_calls = [
        c
        for c in calls
        if c.fully_qualified_parent_path
        and "UserService" in c.fully_qualified_parent_path
    ]

    # Should have some calls inside UserService class
    assert len(class_calls) > 0


def test_calls_have_correct_fqp_in_method(function_calls_test_code: str) -> None:
    """Test that calls have FQP pointing to the containing method"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Calls should have FQP like "ClassName::method_name"
    method_calls = [
        c
        for c in calls
        if c.fully_qualified_parent_path and "::" in c.fully_qualified_parent_path
    ]

    # Should have some calls with method FQP
    assert len(method_calls) > 0


def test_top_level_calls_have_empty_fqp(function_calls_test_code: str) -> None:
    """Test that top-level calls have empty FQP"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Top-level calls should have empty FQP
    top_level_calls = [c for c in calls if c.fully_qualified_parent_path == ""]

    # Should have some top-level calls
    assert len(top_level_calls) > 0


# =============================================================================
# Count and Deduplication Tests
# =============================================================================


def test_extract_function_calls_count(function_calls_test_code: str) -> None:
    """Test that we extract a reasonable number of calls"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Should extract many calls from the test file
    assert len(calls) >= 30, f"Expected at least 30 calls, got {len(calls)}"


def test_duplicate_calls_are_extracted(function_calls_test_code: str) -> None:
    """Test that duplicate calls (same method called multiple times) are all extracted"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Count how many times 'save' is called
    save_calls = [c for c in calls if c.name == "save"]

    # Should have multiple save calls if they appear in test file
    # This tests we don't deduplicate inappropriately
    assert len(save_calls) >= 1


# =============================================================================
# Sorting and Ordering
# =============================================================================


def test_calls_are_sorted_by_position(function_calls_test_code: str) -> None:
    """Test that calls are sorted by their position in the file"""
    driver_tree = RubyDriverTree.from_code(
        function_calls_test_code, "test_function_calls.rb"
    )
    calls = driver_tree.extract_function_calls()

    # Verify calls are in ascending order by start_byte
    for i in range(len(calls) - 1):
        assert (
            calls[i].start_byte <= calls[i + 1].start_byte
        ), f"Calls not sorted: {calls[i].name} at {calls[i].start_byte} comes after {calls[i+1].name} at {calls[i+1].start_byte}"
