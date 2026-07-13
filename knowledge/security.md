# Security Best Practices for Autonomous Engineering Agents

This document outlines mandatory security protocols for this full-stack application. Autonomous agents must strictly adhere to these guidelines when modifying or writing code for the TypeScript/React frontend and Python/FastAPI backend.

---

## 1. Authentication Mechanism

PoolDeals will make use of the OAuth 2 standard, in particular the stateless JWT mechanism, to authenticate users against the backend endpoints.

## 2. Input Validation and Injection Defense

### Backend (Python & FastAPI)

- **No Raw SQL:** Use SQLAlchemy. Always bind variables. Never string-concatenate inputs into queries.
- **Pydantic Validation:** Enforce strict type checking, regex patterns, and value ranges on all incoming request models.
- **Command Injection:** Avoid `os.system` or `subprocess` with `shell=True`. Pass arguments as a list to `subprocess.run()`.
- **Path Traversal:** Use `pathlib.Path.resolve()` to validate that file paths remain within the intended directory.

### Frontend (TypeScript & React)

- **XSS Prevention:** Avoid `dangerouslySetInnerHTML`. If necessary, sanitize data first using `dompurify`.
- **Safe Contexts:** Ensure URL attributes (e.g., `<a href=...`>) are validated to prevent `javascript:` execution.

---

## 3. Authentication, Authorization, and Enumeration

### State and Token Management

- **JWT Handling:** Store access tokens in browser memory. Store refresh tokens in `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
- **Token Verification:** Validate signature, issuer (`iss`), audience (`aud`), and expiration (`exp`) on every backend request.

### Enumeration and Brute Force Defense

- **Generic Errors:** Use ambiguous error messages for auth failures (e.g., "Invalid email or password", not "Email not found").
- **UUIDs for Public IDs:** Never expose auto-incrementing integer IDs in URLs or API responses. Use UUIDv4 to prevent resource enumeration.
- **Rate Limiting:** Implement `slowapi` or custom middleware on sensitive endpoints (`/login`, `/register`, `/password-reset`).

### Access Control

- **Broken Object Level Authorization (BOLA):** Verify that the authenticated user explicitly owns the resource ID they are requesting (typically using hte `sub` claim). Do not rely solely on the presence of a valid JWT.

---

## 4. API Security and Cross-Origin Protocols

### Transport and Headers

- **CORS Policy:** Restrict `Allow-Origins` to specific, trusted domains. Never use `*` in production or combine `*` with credentials.
- **Secure Headers:** Implement `SecureCookiesMiddleware` or custom middleware to inject security headers:
  - `Content-Security-Policy` (CSP)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`

### Data Protection

- **Mass Assignment:** Do not dump raw request payload dicts directly into database models. Explicitly map Pydantic fields to ORM fields.
- **Data Minimization:** Use Pydantic `response_model` configurations to exclude sensitive fields (like password hashes) from API outputs.

---

## 5. Dependencies and Secrets Management

### Secret Handling

- **No Hardcoding:** Never commit API keys, database credentials, or JWT secrets to version control.
- **Configuration:** Utilize Python's `pydantic-settings` to load variables from the environment (`.env`).

### Dependency Security

- **Backend:** Lock versions with `uv.lock`. Run `uv audit` to check for CVEs.
- **Frontend:** Lock versions with `pnpm-lock.yaml`. Run `pnpm audit` to check for CVEs.

---

## 6. Logging and Error Handling

### Secure Logging

- **Sanitization:** Strip passwords, credit card numbers, JWTs, and personally identifiable information (PII) before writing to logs.
- **Framework:** Use standard Python `logging`. Avoid raw `print` statements in production code.

### Error Exposure

- **Production Mode:** Disable FastAPI's automatic documentation (`/docs`, `/redoc`) in production if required by the environment context.
- **Catch-All Handlers:** Suppress raw stack traces in production HTTP responses. Return a generic structure: `{"detail": "An internal error occurred."}`.
