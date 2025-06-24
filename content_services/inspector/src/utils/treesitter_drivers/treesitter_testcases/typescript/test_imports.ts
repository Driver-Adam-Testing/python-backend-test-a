// Test file for TypeScript import/export statements

// Default imports
import React from 'react';
import DefaultExport from './module';

// Named imports
import { Component } from '@angular/core';
import { useState, useEffect } from 'react';
import { readFile, writeFile } from 'fs/promises';

// Named imports with aliases
import { Component as AngularComponent } from '@angular/core';
import { default as DefaultAlias } from './module';

// Namespace imports
import * as fs from 'fs';

// Multiple imports from same module
import DefaultComponent, { namedExport1, namedExport2 } from './component';
import Default, * as Everything from './library';

// Type-only imports
import type { User } from './types';
import type { Config, Settings } from './config';
import type * as Types from './all-types';
import type DefaultType from './default-type';

// Side-effect imports
import './polyfills';
import 'zone.js';

// Dynamic imports
const lazyModule = import('./lazy');
const { LazyComponent } = await import('./lazy-component');

// Import with assertions
import data from './data.json' assert { type: 'json' };

// CommonJS-style imports
import fs2 = require('fs');
const http = require('http');

// Import meta
const url = import.meta.url;
const env = import.meta.env;

// Top-level await with dynamic import
const dynamicModule = await import('./dynamic');
export const dynamicValue = dynamicModule.value;

// Import from node_modules without path
import express from 'express';
import { Request, Response } from 'express';

// Import from scoped packages
import { Component } from '@angular/core';
import { Observable } from '@rxjs/observable';

// Import from nested paths
import { helper } from './utils/helpers';
import Component from './components/Button/Button';

// Import with query parameters (used in some bundlers)
import Worker from './worker.js?worker';
import url from './asset.png?url';

// Import from parent directories
import { parentHelper } from '../helpers';
import { rootUtil } from '../../utils';

// Import index files
import utils from './utils'; // imports from ./utils/index.ts
import components from './components'; // imports from ./components/index.ts

// // Circular import pattern (for testing)
// import { circularDep } from './circular';
// export const circularExport = 'value';
// Export statements
// export { Component };
// export { useState, useEffect };
// 
// // Export with aliases
// export { Component as MyComponent };
// export { default as MyDefault } from './module';
// export { originalName as newName } from './source';
// 
// // Export all
// export * from './utils';
// export * from './types';
// 
// // Export all with namespace
// export * as utilities from './utils';
// export * as Types from './types';
// 
// // Default exports
// export default class DefaultClass {}
// export default function defaultFunction() {}
// export default interface DefaultInterface {}
// 
// // Named exports
// export const API_KEY = 'secret';
// export let counter = 0;
// export var legacyVar = 'old';
// export function helperFunction() {}
// export class ExportedClass {}
// export interface ExportedInterface {}
// export type ExportedType = string;
// export enum ExportedEnum { A, B, C }
// 
// // Type-only exports
// export type { User, Admin } from './types';
// export type { Config };
// 
// // Export declarations
// export declare const declaredConstant: string;
// export declare function declaredFunction(): void;
// export declare class DeclaredClass {}
// 
// // Export assignment (CommonJS style)
// export = { someValue: 42 };
// 
// // Re-exports with renaming
// export { default } from './module';
// export { Component as default } from './component';

// // Combined import and export
// import { Something } from './module';
// export { Something };

// // Exports from different files
// export { utilA, utilB } from './utils';
// export { ServiceA, ServiceB } from './services';

// // Export namespace
// export namespace MyNamespace {
//   export const value = 42;
//   export function helper() {}
// }

// // Export module declaration
// export module MyModule {
//   export interface ModuleInterface {}
// }

// // Abstract class export
// export abstract class AbstractBase {
//   abstract method(): void;
// }

// // Generic exports
// export interface Container<T> {
//   value: T;
// }

// export function genericFunction<T>(value: T): T {
//   return value;
// }

// // Const assertion exports
// export const config = {
//   apiUrl: 'https://api.example.com',
//   timeout: 5000
// } as const;

// // Export with decorators
// @Injectable()
// export class DecoratedService {}

// // Complex export patterns
// export const { destructured1, destructured2 } = getValues();
// export const [first, second] = getTuple();

// // Conditional exports (typically in package.json but showing pattern)
// if (process.env.NODE_ENV === 'production') {
//   module.exports = require('./prod');
// } else {
//   module.exports = require('./dev');
// }

// // Import for side effects only, then re-export
// import './initialize';
// export * from './initialized-module';

// // Importing and exporting types with same name
// import type { Schema } from './schema';
// export type { Schema };

// // Default and named in same statement
// export { default, named1, named2 } from './module';