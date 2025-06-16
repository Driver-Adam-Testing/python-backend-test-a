// Test file for TypeScript class methods

class BasicMethods {
  // Simple methods
  simpleMethod() {
    console.log('simple');
  }
  
  methodWithReturn(): string {
    return 'result';
  }
  
  methodWithParams(a: number, b: string): void {
    console.log(a, b);
  }
  
  methodWithOptional(required: string, optional?: number): boolean {
    return optional !== undefined;
  }
  
  methodWithDefault(value: string = 'default'): string {
    return value;
  }
}

class AccessModifiers {
  public publicMethod(): void {
    console.log('public');
  }
  
  private privateMethod(): string {
    return 'private';
  }
  
  protected protectedMethod(): number {
    return 42;
  }
  
  // No modifier defaults to public
  defaultMethod() {
    return 'default is public';
  }
}

class StaticMethods {
  static simpleStatic(): void {
    console.log('static');
  }
  
  static withParams(x: number, y: number): number {
    return x + y;
  }
  
  private static privateStatic(): string {
    return 'private static';
  }
  
  protected static protectedStatic(): boolean {
    return true;
  }
  
  static #privateStaticField = 'ES2022 private';
  
  static #privateStaticMethod(): string {
    return this.#privateStaticField;
  }
}

class AsyncMethods {
  async simpleAsync(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  async asyncWithReturn(): Promise<string> {
    return 'async result';
  }
  
  async asyncWithParams(url: string): Promise<any> {
    const response = await fetch(url);
    return response.json();
  }
  
  private async privateAsync(): Promise<number> {
    return 42;
  }
  
  static async staticAsync(): Promise<boolean> {
    return true;
  }
  
  async *asyncGenerator(): AsyncGenerator<number> {
    yield 1;
    yield 2;
    yield 3;
  }
}

class GeneratorMethods {
  *simpleGenerator() {
    yield 'a';
    yield 'b';
    yield 'c';
  }
  
  *generatorWithReturn(): Generator<number, string, unknown> {
    yield 1;
    yield 2;
    return 'done';
  }
  
  private *privateGenerator() {
    yield 'private';
  }
  
  static *staticGenerator() {
    yield 'static';
  }
  
  *[Symbol.iterator]() {
    yield* this.simpleGenerator();
  }
}

class GettersSetters {
  private _value: number = 0;
  
  get value(): number {
    return this._value;
  }
  
  set value(newValue: number) {
    this._value = newValue;
  }
  
  get readOnlyProp(): string {
    return 'read only';
  }
  
  private get privateGetter(): boolean {
    return true;
  }
  
  protected set protectedSetter(value: string) {
    console.log(value);
  }
  
  static get staticGetter(): number {
    return 42;
  }
  
  static set staticSetter(value: number) {
    console.log(value);
  }
  
  // Getter/setter with different types
  private _data: string = '';
  
  get data(): string {
    return this._data;
  }
  
  set data(value: string | number) {
    this._data = String(value);
  }
}

class GenericMethods {
  identity<T>(value: T): T {
    return value;
  }
  
  map<T, U>(array: T[], fn: (item: T) => U): U[] {
    return array.map(fn);
  }
  
  constrainedGeneric<T extends string | number>(value: T): T {
    return value;
  }
  
  multipleGenerics<T, U, V>(a: T, b: U, c: V): [T, U, V] {
    return [a, b, c];
  }
  
  static staticGeneric<T>(value: T): T {
    return value;
  }
  
  async asyncGeneric<T>(promise: Promise<T>): Promise<T> {
    return await promise;
  }
  
  // Generic with default
  withDefault<T = string>(value: T): T {
    return value;
  }
}

class MethodOverloading {
  process(value: string): string;
  process(value: number): number;
  process(value: boolean): string;
  process(value: string | number | boolean): string | number {
    if (typeof value === 'boolean') {
      return value.toString();
    }
    return value;
  }
  
  // Multiple overloads
  complex(): void;
  complex(a: string): string;
  complex(a: number, b: number): number;
  complex(a?: string | number, b?: number): void | string | number {
    if (typeof a === 'string') return a;
    if (typeof a === 'number' && typeof b === 'number') return a + b;
    return;
  }
  
  // Static overloading
  static create(): MethodOverloading;
  static create(id: number): MethodOverloading;
  static create(id?: number): MethodOverloading {
    return new MethodOverloading();
  }
}

class SpecialMethods {
  // Constructor
  constructor(private id: string) {}
  
  // Index signatures
  [key: string]: any;
  
  // Computed property methods
  ['computed' + 'Method'](): string {
    return 'computed';
  }
  
  // Symbol methods
  [Symbol.toString](): string {
    return 'SpecialMethods';
  }
  
  [Symbol.toPrimitive](hint: string): string | number {
    return hint === 'number' ? 42 : 'string';
  }
  
  async *[Symbol.asyncIterator]() {
    yield 1;
    yield 2;
  }
  
  // Method with this parameter
  compareWith(this: SpecialMethods, other: SpecialMethods): boolean {
    return this.id === other.id;
  }
  
  // Arrow function property (not technically a method)
  arrowProperty = () => {
    return 'arrow';
  };
  
  // Bound method pattern
  boundMethod = this.regularMethod.bind(this);
  
  regularMethod() {
    return this.id;
  }
}

class DecoratedMethods {
  @log
  simpleDecorated(): void {
    console.log('decorated');
  }
  
  @validate
  @authorize('admin')
  multipleDecorators(data: any): void {
    console.log(data);
  }
  
  @memoize
  expensiveOperation(n: number): number {
    return fibonacci(n);
  }
  
  @deprecated('Use newMethod instead')
  oldMethod(): void {
    console.log('deprecated');
  }
  
  @measureTime
  async timedMethod(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  @autobind
  eventHandler(event: Event): void {
    console.log(this);
  }
}

abstract class AbstractMethods {
  // Abstract methods
  abstract abstractMethod(): void;
  abstract abstractWithParams(x: number): string;
  abstract abstractAsync(): Promise<void>;
  
  // Abstract getters/setters
  abstract get abstractGetter(): number;
  abstract set abstractSetter(value: number);
  
  // Concrete methods
  concreteMethod(): void {
    this.abstractMethod();
  }
  
  // Protected abstract
  protected abstract protectedAbstract(): void;
  
  // Static methods are allowed
  static staticInAbstract(): void {
    console.log('static in abstract');
  }
}

class ConcreteImplementation extends AbstractMethods {
  abstractMethod(): void {
    console.log('implemented');
  }
  
  abstractWithParams(x: number): string {
    return x.toString();
  }
  
  async abstractAsync(): Promise<void> {
    await Promise.resolve();
  }
  
  get abstractGetter(): number {
    return 42;
  }
  
  set abstractSetter(value: number) {
    console.log(value);
  }
  
  protected protectedAbstract(): void {
    console.log('protected implementation');
  }
}

class PrivateFieldMethods {
  #privateField = 'private';
  
  #privateMethod(): string {
    return this.#privateField;
  }
  
  publicAccessor(): string {
    return this.#privateMethod();
  }
  
  static #staticPrivateField = 'static private';
  
  static #staticPrivateMethod(): string {
    return this.#staticPrivateField;
  }
  
  static publicStaticAccessor(): string {
    return this.#staticPrivateMethod();
  }
  
  // Private getter/setter
  #value = 0;
  
  get #privateValue() {
    return this.#value;
  }
  
  set #privateValue(val: number) {
    this.#value = val;
  }
}

class MethodChaining {
  private value = '';
  
  add(text: string): this {
    this.value += text;
    return this;
  }
  
  uppercase(): this {
    this.value = this.value.toUpperCase();
    return this;
  }
  
  trim(): this {
    this.value = this.value.trim();
    return this;
  }
  
  build(): string {
    return this.value;
  }
}

class ComplexMethods {
  // Method returning function
  createCallback(): (x: number) => number {
    return (x) => x * 2;
  }
  
  // Method returning promise of function
  async getAsyncCallback(): Promise<(x: string) => string> {
    return (x) => x.toUpperCase();
  }
  
  // Higher-order method
  higherOrder<T, U>(
    array: T[],
    transform: (item: T) => U
  ): U[] {
    return array.map(transform);
  }
  
  // Curried method
  curry(a: number): (b: number) => (c: number) => number {
    return (b) => (c) => a + b + c;
  }
  
  // Method with destructured parameters
  destructured({ x, y }: { x: number; y: number }): number {
    return x + y;
  }
  
  // Method with rest parameters
  restParams(...args: number[]): number {
    return args.reduce((a, b) => a + b, 0);
  }
  
  // Method with union return type
  unionReturn(type: string): string | number | null {
    switch (type) {
      case 'string': return 'text';
      case 'number': return 42;
      default: return null;
    }
  }
  
  // Type predicate method
  isValid(value: unknown): value is string {
    return typeof value === 'string';
  }
  
  // Assertion method
  assert(condition: unknown): asserts condition {
    if (!condition) {
      throw new Error('Assertion failed');
    }
  }
}

interface MethodInterface {
  requiredMethod(): void;
  optionalMethod?(): void;
  methodWithParams(x: number, y: string): boolean;
}

class InterfaceImplementation implements MethodInterface {
  requiredMethod(): void {
    console.log('required');
  }
  
  optionalMethod(): void {
    console.log('optional implemented');
  }
  
  methodWithParams(x: number, y: string): boolean {
    return x > 0 && y.length > 0;
  }
}

// Methods in object literals
const objectWithMethods = {
  method() {
    return 'method';
  },
  
  async asyncMethod() {
    return 'async';
  },
  
  *generatorMethod() {
    yield 'generator';
  },
  
  get getter() {
    return 'getter';
  },
  
  set setter(value: string) {
    console.log(value);
  },
  
  ['computed' + 'Method']() {
    return 'computed';
  }
};

// Mixin methods
function Loggable<T extends new(...args: any[]) => {}>(Base: T) {
  return class extends Base {
    log(message: string): void {
      console.log(`[${new Date().toISOString()}] ${message}`);
    }
    
    logError(error: Error): void {
      console.error(`[ERROR] ${error.message}`);
    }
  };
}

class BaseClass {
  baseMethod(): string {
    return 'base';
  }
}

class MixinClass extends Loggable(BaseClass) {
  useLogging(): void {
    this.log('Using mixin method');
    this.baseMethod();
  }
}