# Frontend Coding Standards: React & TypeScript (AI Agent Guide)

This document defines the mandatory frontend coding standards for this project. All autonomous AI agents must strictly adhere to these rules when generating, refactoring, or reviewing code.

## 1. Environment & Architecture Core

- **Client-Side Only:** The application is purely client-side rendered (CSR).
- **No Server Features:** Do not use Next.js server-side tools, Remix loaders, or Node.js built-in modules.
- **Web APIs Only:** Rely exclusively on standard browser Web APIs (e.g., `window`, `localStorage`, `fetch`).

## 2. TypeScript Standards

Strict type safety is mandatory. Code must compile under TypeScript `strict: true` settings.

### Type Definitions

- **Prefer Interfaces:** Use `interface` for object structures and component props to leverage declaration merging.
- **Use Types for Unions:** Use `type` only for unions, intersections, primitives (including callback signatures), or tuple definitions.
- **No Implicit Any:** Explicitly type all function arguments, return values, and complex variables.
- **Ban `any`:** Never use the `any` type. Use `unknown` if the type is truly dynamic, then narrow it down.
- **Type Assertions:** Avoid `as Type` assertions. Use type guards or explicit validation instead.

### Runtime validation

Use Zod for validating any input payloads or response bodies returned by the backend. Where missing, write the Zod schemas based upon the response shapes provided by the backend's endpoints.

### Modern Features

- **Optional Chaining:** Use `?.` instead of verbose logical `&&` checks for nested properties.
- **Nullish Coalescing:** Use `??` instead of `||` to provide default values without overriding valid falsy values (like `0` or `""`).
- **Enums Banned:** Do not use `enum`. Use const assertions instead:

  ```typescript
  export const USER_ROLES = {
    ADMIN: "admin",
    USER: "user",
  } as const;

  export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];
  ```

## 3. React Development Rules

### Component Architecture

- **Functional Components:** Use arrow functions with explicit return types for all components.
- **File Structure:** One component per file. Name the file using PascalCase (e.g., `Button.tsx`).
- **Destructured Props:** Destructure component props directly in the function signature.
- **No `React.FC`:** Do not use `React.FC` or `React.FunctionComponent`. Type props directly:

  ```typescript
  interface ButtonProps {
    label: string;
    onClick: () => void;
  }

  export const Button = ({ label, onClick }: ButtonProps): React.JSX.Element => {
    return <button onClick={onClick}>{label}</button>;
  };
  ```

For components that render their parent's children, support a `children` property of type `React.ReactNode`. **Do not use `React.PropsWithChildren`.**

### State & Hooks

- **Custom Hooks:** Extract complex stateful logic, data fetching, or side effects into custom hooks.
- **Hook Dependency Arrays:** Always populate hook dependency arrays completely. Never skip dependencies.
- **State Locality:** Keep state as local as possible. Do not lift state up prematurely.

### Performance Minimisation

- **Key Prop Stability:** Always use stable, unique identifiers (like database IDs) for list `key` props. Never use array indices.
- **Memoization:** Use `useMemo` and `useCallback` only for heavy computations or to prevent broken dependency chains. Do not use them blindly on every function or value.

## 4. Code Cleanliness & Security

- **No Direct DOM Manipulation:** Always interact with elements via React `refs` or state. Never use `document.getElementById`.
- **Safe HTML:** Never use `dangerouslySetInnerHTML` unless explicitly instructed and wrapped in a sanitisation helper.
- **Resource Cleanup:** Always return a cleanup function in `useEffect` hooks when setting up event listeners, intervals, or subscriptions.

## 5. Tooling

- **Use pnpm for package management.** Do **not** use vanilla npm or Yarn.
