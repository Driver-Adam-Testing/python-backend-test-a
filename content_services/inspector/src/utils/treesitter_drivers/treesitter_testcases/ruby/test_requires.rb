# Test file for Ruby requires

# Standard library requires (absolute)
require 'json'
require 'yaml'
require 'active_support'
require "fileutils"

# Requires with nested paths (absolute)
require 'active_support/core_ext'
require 'rails/all'
require "rack/utils"

# Simple require_relative (relative)
require_relative '../models/user'
require_relative './helper'
require_relative 'config/database'

# require_relative with double quotes (relative)
require_relative "../lib/constants"
require_relative "./services/auth_service"

# require_relative without ./ prefix (relative)
require_relative 'utils'
require_relative 'validators/email_validator'

# require_relative with deep paths (relative)
require_relative '../../shared/logger'
require_relative '../../../common/base'

# Mixed absolute and relative
require 'rack'
require_relative 'lib/utils'
require 'sinatra'
require_relative '../app'

# Edge cases - requires with .rb extension (should strip it)
require 'bundler.rb'
require_relative './config.rb'

# Single vs double quotes mix
require 'nokogiri'
require "open-uri"
require_relative 'helpers'
require_relative "../models/post"

# Requires inside class
class MyClass
  require 'set'
  require_relative 'class_helper'
end

# Requires inside module
module MyModule
  require 'forwardable'
  require_relative 'module_helper'
end

# Requires inside method
def my_method
  require 'tmpdir'
  require_relative 'method_helper'
end

# Requires inside class method
class MyClass
  def self.class_method
    require 'benchmark'
    require_relative 'benchmark_helper'
  end
  
  def instance_method
    require 'digest'
    require_relative 'digest_helper'
  end
end
