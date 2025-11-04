// Test file for TypeScript interfaces and type aliases

// Basic interfaces
interface InterfaceWithOptional {
  required: string;
  optional?: number;
  optionalMethod?(): void;
}

// Readonly properties
interface ReadonlyInterface {
  readonly id: string;
  readonly data: number[];
  readonly nested: {
    readonly value: string;
  };
}

// Index signatures
interface StringIndex {
  [key: string]: any;
}

interface NumberIndex {
  [index: number]: string;
}

interface MixedIndex {
  [key: string]: string | number;
  [index: number]: string;
  length: number;
}

// Interface inheritance
interface Animal {
  name: string;
  age: number;
}

interface Dog extends Animal {
  breed: string;
  bark(): void;
}

// Multiple inheritance
interface Flyable {
  fly(): void;
  altitude: number;
}

interface Swimmable {
  swim(): void;
  depth: number;
}

interface Duck extends Animal, Flyable, Swimmable {
  quack(): void;
}

// Generic interfaces
interface Pair<T, U> {
  first: T;
  second: U;
}

// Nested interfaces
interface OuterInterface {
  outer: string;
  inner: {
    nested: string;
    deep: {
      value: number;
    };
  };
}

// Interface merging
interface MergedInterface {
  property1: string;
}

interface MergedInterface {
  property2: number;
}

interface MergedInterface {
  method(): void;
}



// Module augmentation interfaces
declare module 'express' {
  interface Request {
    user?: {
      id: string;
      name: string;
    };
  }
}

// Global augmentation
declare global {
  interface Window {
    myGlobal: string;
  }

  interface Array<T> {
    customMethod(): T[];
  }
}

// Ambient interfaces
declare interface AmbientInterface {
  ambientProperty: string;
  ambientMethod(): void;
}

// Type-only exports
export interface ExportedInterface {
  exported: true;
}
