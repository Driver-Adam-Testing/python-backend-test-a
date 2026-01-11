// Test file for TypeScript class definitions

// Basic class
class SimpleClass {
  constructor() {
    console.log('Simple class');
  }
}

// Class with properties
class ClassWithProperties {
  public publicProp: string;
  private privateProp: number;
  protected protectedProp: boolean;
  readonly readonlyProp: string;
  static staticProp: number = 42;

  constructor() {
    this.publicProp = 'public';
    this.privateProp = 1;
    this.protectedProp = true;
    this.readonlyProp = 'readonly';
  }
}

// Class with methods
class ClassWithMethods {
  publicMethod(): void {
    console.log('public method');
  }

  private privateMethod(): string {
    return 'private';
  }

  protected protectedMethod(): number {
    return 42;
  }

  static staticMethod(): void {
    console.log('static method');
  }
}

// Class with parameter properties
class ParameterProperties {
  constructor(
    public name: string,
    private age: number,
    protected email: string,
    readonly id: string
  ) {}
}

// Class with getters and setters
class GettersSetters {
  private _value: number = 0;

  get value(): number {
    return this._value;
  }

  set value(newValue: number) {
    this._value = newValue;
  }

  get readOnly(): string {
    return 'readonly';
  }

  private get privateGetter(): number {
    return 42;
  }

  protected set protectedSetter(value: string) {
    console.log(value);
  }
}

// Class inheritance
class Animal {
  name: string;

  constructor(name: string) {
    this.name = name;
  }

  speak(): void {
    console.log(`${this.name} makes a sound`);
  }
}

class Dog extends Animal {
  breed: string;

  constructor(name: string, breed: string) {
    super(name);
    this.breed = breed;
  }

  speak(): void {
    console.log(`${this.name} barks`);
  }

  wagTail(): void {
    console.log('Wagging tail');
  }
}

// Abstract class
abstract class Shape {
  abstract area(): number;
  abstract perimeter(): number;

  describe(): string {
    return `Area: ${this.area()}, Perimeter: ${this.perimeter()}`;
  }
}

class Circle extends Shape {
  constructor(private radius: number) {
    super();
  }

  area(): number {
    return Math.PI * this.radius ** 2;
  }

  perimeter(): number {
    return 2 * Math.PI * this.radius;
  }
}

// Generic class
class Container<T> {
  private value: T;

  constructor(value: T) {
    this.value = value;
  }

  getValue(): T {
    return this.value;
  }

  setValue(value: T): void {
    this.value = value;
  }
}

class TwoTypeContainer<T, U> {
  constructor(
    private first: T,
    private second: U
  ) {}

  getFirst(): T {
    return this.first;
  }

  getSecond(): U {
    return this.second;
  }
}

// Generic class with constraints
class ConstrainedContainer<T extends { length: number }> {
  constructor(private value: T) {}

  getLength(): number {
    return this.value.length;
  }
}

// // Class implementing interface
// interface Flyable {
//   fly(): void;
//   altitude: number;
// }

// interface Swimmable {
//   swim(): void;
//   depth: number;
// }

class Bird implements Flyable {
  altitude: number = 0;

  fly(): void {
    console.log('Flying');
    this.altitude = 100;
  }
}

class Duck extends Bird implements Swimmable {
  depth: number = 0;

  swim(): void {
    console.log('Swimming');
    this.depth = 5;
  }
}

// Multiple interface implementation
class Amphibian implements Flyable, Swimmable {
  altitude: number = 0;
  depth: number = 0;

  fly(): void {
    this.altitude = 50;
  }

  swim(): void {
    this.depth = 10;
  }
}

// Class with decorators
@Component({
  selector: 'app-root',
  template: '<div>App</div>'
})
class AppComponent {
  @Input() title: string = 'My App';
  @Output() clicked = new EventEmitter();

  @HostListener('click', ['$event'])
  onClick(event: MouseEvent): void {
    this.clicked.emit(event);
  }

  @ViewChild('myDiv')
  divElement!: ElementRef;
}

// Class with method decorators
class ServiceClass {
  @Log()
  @Validate()
  performAction(data: any): void {
    console.log('Performing action', data);
  }

  @Deprecated('Use newMethod instead')
  oldMethod(): void {
    console.log('Old method');
  }

  @Memoize()
  expensiveOperation(n: number): number {
    return fibonacci(n);
  }
}

// Static members and blocks
class StaticExample {
  static count: number = 0;
  static readonly VERSION = '1.0.0';
  private static instance: StaticExample;

  static {
    // Static initialization block
    this.count = 1;
    console.log('Static block executed');
  }

  static getInstance(): StaticExample {
    if (!this.instance) {
      this.instance = new StaticExample();
    }
    return this.instance;
  }

  static resetInstance(): void {
    this.instance = null!;
  }
}

// Private fields (ES2022)
class PrivateFields {
  #privateField: string = 'private';
  #privateMethod(): string {
    return this.#privateField;
  }

  static #privateStatic: number = 42;

  static #privateStaticMethod(): number {
    return this.#privateStatic;
  }

  getPrivate(): string {
    return this.#privateMethod();
  }

  static getStaticPrivate(): number {
    return this.#privateStaticMethod();
  }
}

// Class expressions
const ClassExpression = class {
  method(): string {
    return 'class expression';
  }
};

const NamedClassExpression = class MyClass {
  static className = 'MyClass';

  getName(): string {
    return MyClass.className;
  }
};

// Anonymous class extending
const ExtendedAnonymous = class extends Animal {
  constructor() {
    super('Anonymous');
  }

  speak(): void {
    console.log('Anonymous speaks');
  }
};

// Nested classes
class Outer {
  static NestedClass = class {
    nestedMethod(): string {
      return 'nested';
    }
  };

  createInner() {
    return new Outer.NestedClass();
  }
}

// Mixin pattern
type Constructor<T = {}> = new (...args: any[]) => T;

function Timestamped<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    timestamp = Date.now();

    getTimestamp() {
      return this.timestamp;
    }
  };
}

function Tagged<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    tags: string[] = [];

    addTag(tag: string) {
      this.tags.push(tag);
    }
  };
}

class BasicClass {
  id: number;
  constructor(id: number) {
    this.id = id;
  }
}

const MixedClass = Tagged(Timestamped(BasicClass));
const mixedInstance = new MixedClass(1);

// Async methods
class AsyncClass {
  async fetchData(): Promise<any> {
    const response = await fetch('/api/data');
    return response.json();
  }

  async *asyncGenerator(): AsyncGenerator<number> {
    yield 1;
    yield 2;
    yield 3;
  }

  private async privateAsync(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  static async staticAsync(): Promise<string> {
    return 'static async';
  }
}

// Generator methods
class GeneratorClass {
  *generator(): Generator<number> {
    yield 1;
    yield 2;
    yield 3;
  }

  *[Symbol.iterator]() {
    yield* this.generator();
  }
}

// Index signatures and computed properties
const propertyName = 'dynamicProp';

class IndexedClass {
  [key: string]: any;
  [index: number]: string;

  [propertyName]: string = 'dynamic value';

  ['computed' + 'Property'](): string {
    return 'computed';
  }
}

// This type
class FluentAPI {
  private value: string = '';

  setValue(value: string): this {
    this.value = value;
    return this;
  }

  append(text: string): this {
    this.value += text;
    return this;
  }

  build(): string {
    return this.value;
  }
}

// Constructor overloads
class OverloadedConstructor {
  name: string;
  age: number;

  constructor(name: string);
  constructor(name: string, age: number);
  constructor(name: string, age?: number) {
    this.name = name;
    this.age = age ?? 0;
  }
}

// Method overloads
class OverloadedMethods {
  process(value: string): string;
  process(value: number): number;
  process(value: string | number): string | number {
    return value;
  }

  static create(): OverloadedMethods;
  static create(id: number): OverloadedMethods;
  static create(id?: number): OverloadedMethods {
    return new OverloadedMethods();
  }
}

// Classes as namespaces
class ClassNamespace {
  static Utils = class {
    static helper(): string {
      return 'helper';
    }
  };

  static Types = {
    TypeA: class { a: string = 'A'; },
    TypeB: class { b: string = 'B'; }
  };
}

// Declaration merging with classes
class MergedClass {
  method(): void {
    console.log('method');
  }
}

interface MergedClass {
  additionalProp: string;
  additionalMethod(): void;
}

// Generic constraints with keyof
class PropertyAccess<T> {
  constructor(private obj: T) {}

  get<K extends keyof T>(key: K): T[K] {
    return this.obj[key];
  }

  set<K extends keyof T>(key: K, value: T[K]): void {
    this.obj[key] = value;
  }
}

// Conditional types in classes
class ConditionalClass<T> {
  value: T extends string ? string[] : T;

  constructor(value: T extends string ? string[] : T) {
    this.value = value;
  }
}

// Abstract generic class
abstract class AbstractGeneric<T> {
  abstract process(value: T): T;

  execute(value: T): T {
    return this.process(value);
  }
}

class ConcreteGeneric extends AbstractGeneric<string> {
  process(value: string): string {
    return value.toUpperCase();
  }
}

// Class with symbol members
class SymbolClass {
  [Symbol.toStringTag] = 'SymbolClass';

  [Symbol.iterator]() {
    return [1, 2, 3][Symbol.iterator]();
  }

  [Symbol.hasInstance](instance: any): boolean {
    return instance instanceof SymbolClass;
  }
}

// Brand checking with private fields
class BrandedClass {
  #brand: unique symbol;

  static isBrandedClass(obj: any): obj is BrandedClass {
    return #brand in obj;
  }
}

// Readonly class
class ReadonlyClass {
  readonly id: string;
  readonly data: ReadonlyArray<number>;
  readonly config: Readonly<{ url: string; timeout: number }>;

  constructor(id: string) {
    this.id = id;
    this.data = [1, 2, 3];
    this.config = { url: '/api', timeout: 5000 };
  }
}

// Class with assertion signatures
class Validator {
  assert(condition: unknown, message?: string): asserts condition {
    if (!condition) {
      throw new Error(message || 'Assertion failed');
    }
  }

  assertIsString(value: unknown): asserts value is string {
    this.assert(typeof value === 'string', 'Value must be a string');
  }
}
