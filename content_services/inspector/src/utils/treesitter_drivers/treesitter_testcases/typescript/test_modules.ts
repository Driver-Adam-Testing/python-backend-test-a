// Test file for TypeScript modules and namespaces

// Basic namespace
namespace BasicNamespace {
  export const value = 42;
  export function helper() {
    return 'helper';
  }
  export class NamespaceClass {
    method() {
      return 'namespace class';
    }
  }
}

// Nested namespaces
namespace OuterNamespace {
  export namespace InnerNamespace {
    export interface InnerInterface {
      prop: string;
    }
    
    export function innerFunction() {
      return 'inner';
    }
    
    export namespace DeepNamespace {
      export const deep = 'deep value';
    }
  }
  
  export const outerValue = OuterNamespace.InnerNamespace.DeepNamespace.deep;
}

// Module declaration
module MyModule {
  export interface ModuleInterface {
    id: string;
    name: string;
  }
  
  export class ModuleClass implements ModuleInterface {
    constructor(public id: string, public name: string) {}
  }
  
  export function createInstance(id: string): ModuleClass {
    return new ModuleClass(id, 'Module');
  }
}

// Namespace with private members
namespace PrivateNamespace {
  const privateConst = 'private';
  let privateLet = 42;
  
  function privateFunction() {
    return privateConst;
  }
  
  export function publicFunction() {
    return privateFunction();
  }
  
  export class PublicClass {
    getPrivate() {
      return privateLet;
    }
  }
}

// Namespace merging
namespace MergedNamespace {
  export interface MergedInterface {
    prop1: string;
  }
}

namespace MergedNamespace {
  export interface MergedInterface {
    prop2: number;
  }
  
  export function mergedFunction() {
    return 'merged';
  }
}

// Global augmentation
declare global {
  interface Window {
    myGlobal: {
      value: string;
      method(): void;
    };
  }
  
  namespace NodeJS {
    interface Global {
      customGlobal: string;
    }
  }
}

// Module augmentation
declare module 'express' {
  interface Request {
    user?: {
      id: string;
      name: string;
      role: string;
    };
    session?: {
      token: string;
    };
  }
  
  interface Response {
    sendJson(data: any): void;
  }
}

// Ambient module declaration
declare module '*.json' {
  const value: any;
  export default value;
}

declare module '*.css' {
  const styles: { [key: string]: string };
  export default styles;
}

declare module 'legacy-library' {
  export function legacyFunction(x: number): string;
  export class LegacyClass {
    constructor(name: string);
    method(): void;
  }
  export const LEGACY_CONSTANT: number;
}

// Wildcard module declarations
declare module 'server/*' {
  export interface ServerModule {
    start(): void;
    stop(): void;
  }
}

// Namespace as type
namespace TypeNamespace {
  export type ID = string;
  export type Status = 'active' | 'inactive';
  
  export interface User {
    id: ID;
    status: Status;
  }
}

type UserId = TypeNamespace.ID;
type UserType = TypeNamespace.User;

// Namespace with enum
namespace EnumNamespace {
  export enum Direction {
    Up,
    Down,
    Left,
    Right
  }
  
  export function move(dir: Direction) {
    console.log('Moving', Direction[dir]);
  }
}

// Complex namespace with all member types
namespace ComplexNamespace {
  // Variables
  export const constant = 'const value';
  export let variable = 'let value';
  export var legacyVar = 'var value';
  
  // Functions
  export function normalFunction() {
    return 'function';
  }
  
  export const arrowFunction = () => 'arrow';
  
  export async function asyncFunction() {
    return 'async';
  }
  
  // Classes
  export class NormalClass {
    method() {
      return 'class method';
    }
  }
  
  export abstract class AbstractClass {
    abstract abstractMethod(): void;
  }
  
  // Interfaces
  export interface NormalInterface {
    prop: string;
  }
  
  export interface GenericInterface<T> {
    value: T;
  }
  
  // Type aliases
  export type TypeAlias = string | number;
  export type GenericType<T> = T[];
  
  // Enums
  export enum NormalEnum {
    A,
    B,
    C
  }
  
  export const enum ConstEnum {
    X = 10,
    Y = 20
  }
  
  // Nested namespace
  export namespace Nested {
    export const nestedValue = 'nested';
  }
}

// Import/export within namespace
namespace ImportExportNamespace {
  // Can't use ES6 import/export, but can reference other namespaces
  export import Alias = ComplexNamespace.NormalClass;
  export import EnumAlias = EnumNamespace.Direction;
  
  export class ExtendedClass extends Alias {
    extendedMethod() {
      return super.method() + ' extended';
    }
  }
}

// Namespace in a class
class ClassWithNamespace {
  static Namespace = class {
    static value = 'class namespace';
    static method() {
      return 'method in class namespace';
    }
  };
  
  useNamespace() {
    return ClassWithNamespace.Namespace.value;
  }
}

// Module with side effects
module SideEffectModule {
  // Side effect - runs when module loads
  console.log('Module loaded');
  
  export function initialize() {
    console.log('Initialized');
  }
  
  // IIFE in module
  (() => {
    console.log('Module IIFE');
  })();
}

// Namespace extending a class
class BaseForNamespace {
  baseMethod() {
    return 'base';
  }
}

namespace ExtendingNamespace {
  export class Extended extends BaseForNamespace {
    extendedMethod() {
      return this.baseMethod() + ' from namespace';
    }
  }
}

// Declaration merging with namespace and function
function MergedFunction(x: number): number {
  return x * 2;
}

namespace MergedFunction {
  export const version = '1.0.0';
  export function helper() {
    return 'helper';
  }
}

// Declaration merging with namespace and class
class MergedClass {
  method() {
    return 'class method';
  }
}

namespace MergedClass {
  export const staticValue = 'static from namespace';
  export interface RelatedInterface {
    prop: string;
  }
}

// Declaration merging with namespace and enum
enum MergedEnum {
  A,
  B,
  C
}

namespace MergedEnum {
  export function isValid(value: number): value is MergedEnum {
    return value >= 0 && value <= 2;
  }
}

// Export namespace
export namespace ExportedNamespace {
  export const value = 'exported';
  export function helper() {
    return 'exported helper';
  }
}

// Export module
export module ExportedModule {
  export interface ExportedInterface {
    id: string;
  }
}

// Default export with namespace (pattern)
namespace DefaultNamespace {
  export const value = 'default';
}
export default DefaultNamespace;

// Ambient namespace
declare namespace AmbientNamespace {
  const ambientValue: string;
  function ambientFunction(): void;
  
  interface AmbientInterface {
    prop: string;
  }
  
  namespace Nested {
    const nestedAmbient: number;
  }
}

// UMD module pattern
declare namespace UMDLibrary {
  export function method(): void;
  export const value: string;
}

declare module 'umd-library' {
  export = UMDLibrary;
}

// Conditional namespace members
namespace ConditionalNamespace {
  export type IsProduction = typeof process.env.NODE_ENV extends 'production' ? true : false;
  
  export const config = {
    debug: true as const
  };
}

// Type-only namespace exports
namespace TypeOnlyNamespace {
  export type OnlyType = string;
  export interface OnlyInterface {
    prop: string;
  }
}

export type { TypeOnlyNamespace };

// Using namespace types
const namespaceUsage: BasicNamespace.NamespaceClass = new BasicNamespace.NamespaceClass();
const enumUsage: EnumNamespace.Direction = EnumNamespace.Direction.Up;

// Triple-slash directives
/// <reference path="types.d.ts" />
/// <reference types="node" />
/// <reference lib="es2015" />

// Module resolution demonstration
import * as ModuleNamespace from './module';
import { ExportedNamespace as Renamed } from './this-file';

// Dynamic namespace member access
const dynamicAccess = BasicNamespace['value'];
const dynamicMethod = BasicNamespace['helper'];