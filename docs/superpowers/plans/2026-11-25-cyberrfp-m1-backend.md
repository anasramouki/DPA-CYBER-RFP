# CyberRFP Maroc Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Milestone 1 of the CyberRFP Maroc backend in `backend-next/` using Next.js 16 (App Router + TypeScript), Neon Postgres with Drizzle ORM, and Better Auth supporting both mobile/SPA `Authorization: Bearer` tokens and same-origin HttpOnly cookies.

**Architecture:** All new backend code lives inside `backend-next/` (keeping the existing Python FastAPI app in `src/` untouched). Database and auth clients initialize lazily (`getDb()`, `getAuth()`) to prevent build-time `DATABASE_URL` crashes and avoid JS `Proxy` issues, while `src/proxy.ts` handles CORS allowlisting and security headers for `/api/*`.

**Tech Stack:** Next.js 16 (App Router), TypeScript, Node.js 24 LTS (Fluid Compute target), Neon Postgres (`@neondatabase/serverless`), Drizzle ORM (`drizzle-orm/neon-http`, `drizzle-kit`), Better Auth (`better-auth` with `bearer()` + `nextCookies()`), Zod, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-25-cyberrfp-m1-backend-design.md`

## Global Constraints

- **Workspace isolation:** All Milestone 1 backend files live under `backend-next/`; do NOT modify `src/`, `tests/`, `docs/plan.md`, `requirements.txt`, or root `.env`.
- **Target runtime:** Default Node.js Fluid Compute runtime — never add `export const runtime = 'edge'`. Next.js 16 uses `src/proxy.ts` exporting `proxy(request)` (not `middleware.ts`).
- **Lazy DB & Auth initialization:** Never instantiate `neon(process.env.DATABASE_URL!)` or `betterAuth(...)` at module evaluation time, and never wrap DB clients in JS `Proxy`. Always expose `getDb()` and `getAuth()`.
- **RBAC & profile security:** `role` is strictly `'analyst' | 'admin'` (server default `'analyst'`, `input: false` on registration); public `/api/auth/register` and `PATCH /api/profile` must never accept or mutate `role`, `id`, `emailVerified`, or `createdAt`.
- **Auth modes:** Primary cross-origin/mobile auth uses `Authorization: Bearer <token>` via Better Auth `bearer()` (no `jwt()`/`jwks` in M1 so `POST /api/auth/logout` revokes sessions immediately); same-origin HttpOnly cookies also work via `nextCookies()`.
- **API contracts:**
  - `SafeUser`: `{ id, email, fullName, role, jobTitle, company, whatsappPhone, whatsappAlertsEnabled, emailAlertsEnabled, preferredLanguage, createdAt, updatedAt }` (`fullName` backed by `user.name`).
  - Error envelope: `{ error: { code: "VALIDATION_ERROR" | "UNAUTHORIZED" | "FORBIDDEN" | "CONFLICT" | "INTERNAL_ERROR", message: string, details?: Record<string, string[]> } }`.
  - E.164 WhatsApp phone validation: `^\+[1-9]\d{6,14}$` (or `null` when cleared).
- **Version-matched docs:** Read `node_modules/next/dist/docs/` before writing Next.js 16 Route Handlers or `proxy.ts`, and verify exact `better-auth` imports against `node_modules/better-auth`.
- **Secrets:** Never print `.env.local` values or secrets in logs, code, or reports.

## Review Focus

- **Build-time missing env safety:** Running `next build` or importing route modules when `DATABASE_URL` or `BETTER_AUTH_SECRET` is unset at build time must not throw during static module evaluation.
- **Mass-assignment / privilege escalation on registration & profile:** Sending `role: "admin"`, `id`, `emailVerified: true`, or unknown keys in `POST /api/auth/register` or `PATCH /api/profile` must be rejected (`400 VALIDATION_ERROR`) or ignored by server-enforced defaults, never elevating privileges.
- **Cross-user BOLA / IDOR isolation:** User A presenting a valid Bearer token or cookie cannot read or update User B's profile regardless of query params or JSON body fields; revoked tokens after `POST /api/auth/logout` immediately return `401 UNAUTHORIZED` on `/api/profile`.
- **CORS credential safety:** Origins outside `ALLOWED_ORIGINS` must never receive `Access-Control-Allow-Origin: *` paired with `Access-Control-Allow-Credentials: true`; allowed origins receive exact origin echo + `Vary: Origin`.
- **Phone & email domain validation edge cases:** Invalid WhatsApp numbers (missing `+`, letters, too short/long) return `400 VALIDATION_ERROR`, clearing `whatsappPhone` with `null` succeeds, and non-allowlisted domains return `403 FORBIDDEN` when `ALLOWED_EMAIL_DOMAINS` is set.

---

### Task 1: Next.js 16 Scaffold, Dependencies, Env/HTTP Helpers & CORS Proxy

**Files:**
- Create: `backend-next/package.json`
- Create: `backend-next/tsconfig.json`
- Create: `backend-next/next.config.ts`
- Create: `backend-next/vitest.config.ts`
- Create: `backend-next/.env.example`
- Create: `backend-next/src/lib/env.ts`
- Create: `backend-next/src/lib/http.ts`
- Create: `backend-next/src/proxy.ts`
- Test: `backend-next/tests/http-and-proxy.test.ts`

**Interfaces:**
- Consumes: Environment variables (`DATABASE_URL`, `BETTER_AUTH_SECRET`, `BETTER_AUTH_URL`, `ALLOWED_ORIGINS`, `ALLOWED_EMAIL_DOMAINS`).
- Produces:
  - `getEnv()` in `src/lib/env.ts`
  - `apiSuccess(data, status?, headers?)`, `apiError(code, message, status, details?)`, `parseJsonBody(request, schema)`, `toSafeUser(row)` in `src/lib/http.ts`
  - `proxy(request: NextRequest)` and `config` in `src/proxy.ts`

- [ ] **Step 1: Initialize `backend-next/package.json` and install dependencies**

Create `backend-next/package.json` with scripts (`dev`, `build`, `start`, `typecheck`, `test`, `db:push`, `db:generate`, `db:seed`) and install:
- Runtime: `next`, `react`, `react-dom`, `better-auth`, `drizzle-orm`, `@neondatabase/serverless`, `zod`, `@vercel/functions`
- Dev: `typescript`, `@types/node`, `@types/react`, `@types/react-dom`, `drizzle-kit`, `tsx`, `dotenv-cli`, `vitest`
Verify installed `node_modules/next/dist/docs/` for `proxy.ts` and Route Handler conventions.

- [ ] **Step 2: Create configuration files (`tsconfig.json`, `next.config.ts`, `vitest.config.ts`, `.env.example`)**

Configure `@/*` -> `./src/*` in `tsconfig.json` and `vitest.config.ts` (`environment: 'node'`). Document all Milestone 1 env vars (empty values for secrets) in `.env.example`.

- [ ] **Step 3: Write failing tests for `env.ts`, `http.ts`, and `proxy.ts`**

In `backend-next/tests/http-and-proxy.test.ts`:
- `test_error_envelope_and_safe_user_mapping`: asserts `apiError('VALIDATION_ERROR', 'Bad input', 400, { email: ['Invalid'] })` returns JSON `{ error: { code: 'VALIDATION_ERROR', message: 'Bad input', details: { email: ['Invalid'] } } }` and `toSafeUser` omits any sensitive/extra DB columns while mapping `name` -> `fullName` and ISO timestamps.
- `test_allowed_email_domains_parsing`: asserts `isEmailDomainAllowed('user@dpg-cyber.com', 'dpg-cyber.com,example.ma')` returns `true`, `'user@gmail.com'` returns `false`, and empty config allows any domain.
- `test_proxy_cors_allowlist_and_preflight`: asserts `OPTIONS /api/health` from allowed origin returns `204` with exact `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials: true`, `Vary: Origin`, and disallowed origin does NOT get `Access-Control-Allow-Origin` echoed. Also checks security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).

- [ ] **Step 4: Run test to verify it fails**

Run: `npx vitest run tests/http-and-proxy.test.ts` inside `backend-next/`
Expected: FAIL because `src/lib/env.ts`, `src/lib/http.ts`, and `src/proxy.ts` do not exist yet.

- [ ] **Step 5: Implement `src/lib/env.ts`, `src/lib/http.ts`, and `src/proxy.ts`**

- `src/lib/env.ts`: Runtime env readers (`getDatabaseUrl()`, `getBetterAuthSecret()`, `getAllowedOrigins()`, `isEmailDomainAllowed(email)`). Never throws at module import time.
- `src/lib/http.ts`: `SafeUser` type, `ApiErrorCode` union, `apiSuccess`, `apiError`, `parseJsonBody` (handles invalid JSON + Zod `strict()` errors cleanly into `VALIDATION_ERROR` with `fieldErrors`), `toSafeUser(row)`.
- `src/proxy.ts`: Exports `proxy(request: NextRequest)` handling `/api/:path*` preflight `OPTIONS` and attaching CORS headers for matching `ALLOWED_ORIGINS` plus `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

- [ ] **Step 6: Run tests and TypeScript check to verify Task 1 passes**

Run: `npx vitest run tests/http-and-proxy.test.ts && npx tsc --noEmit`
Expected: PASS (all tests passing, zero TS errors).

---

### Task 2: Neon PostgreSQL Drizzle Schema, Lazy DB Client, Seed & `/api/health`

**Files:**
- Create: `backend-next/drizzle.config.ts`
- Create: `backend-next/src/db/schema.ts`
- Create: `backend-next/src/db/index.ts`
- Create: `backend-next/src/db/seed.ts`
- Create: `backend-next/src/app/api/health/route.ts`
- Test: `backend-next/tests/db-and-health.test.ts`

**Interfaces:**
- Consumes: `getDatabaseUrl()` from `src/lib/env.ts`, `apiSuccess` / `apiError` from `src/lib/http.ts`.
- Produces:
  - Tables in `src/db/schema.ts`: `user`, `session`, `account`, `verification`, `sources`, `tenders` + inferred types (`UserRow`, `SourceRow`, `TenderRow`).
  - `getDb()` and `checkDatabaseHealth()` in `src/db/index.ts`.
  - `DEFAULT_SOURCES` and `seedSources(db)` in `src/db/seed.ts`.
  - `GET /api/health` in `src/app/api/health/route.ts`.

- [ ] **Step 1: Write failing tests for DB lazy init, seed idempotency, and `/api/health`**

In `backend-next/tests/db-and-health.test.ts`:
- `test_schema_exports_required_tables`: asserts `user`, `session`, `account`, `verification`, `sources`, `tenders` exist with expected columns (`role`, `jobTitle`, `whatsappPhone`, `whatsappAlertsEnabled`, `emailAlertsEnabled`, `preferredLanguage`, `dedupHash`, `isHighPriority`).
- `test_get_db_throws_only_on_call_when_missing_url`: asserts importing `src/db/index.ts` without `DATABASE_URL` succeeds, and calling `getDb()` throws an explicit configuration error.
- `test_seed_sources_contains_all_7_moroccan_portals`: asserts `DEFAULT_SOURCES` contains all 7 required slugs (`pmmp`, `al-barid-bank`, `sorec`, `atlantic-re`, `autoroutes-du-maroc`, `laprophan`, `ofppt`) and `seedSources(mockDb)` executes `onConflictDoUpdate` / idempotent upserts for each.
- `test_health_route_returns_200_when_db_ok_and_503_when_db_fails`: mocks `checkDatabaseHealth()` to verify `GET /api/health` returns `200 { status: 'ok', database: 'connected' }` vs `503`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/db-and-health.test.ts`
Expected: FAIL because `src/db/*` and `src/app/api/health/route.ts` do not exist yet.

- [ ] **Step 3: Implement `drizzle.config.ts`, `src/db/schema.ts`, `src/db/index.ts`, `src/db/seed.ts`, and `src/app/api/health/route.ts`**

Verify Better Auth v1.x Drizzle Postgres table/column expectations against `node_modules/better-auth` before finalizing `src/db/schema.ts`. Use `neon(getDatabaseUrl())` + `drizzle(sql, { schema })` lazily inside `getDb()` (no `Proxy`). Use `export const dynamic = 'force-dynamic'` in `src/app/api/health/route.ts`.

- [ ] **Step 4: Run tests, push schema to live Neon Postgres, and run idempotent seed**

Run:
- `npx vitest run tests/db-and-health.test.ts`
- `npx dotenv -e .env.local -- npx drizzle-kit push --force` (or `--yes` / verified CLI flag)
- `npx dotenv -e .env.local -- npx tsx src/db/seed.ts`
Expected: PASS, schema synced to `cyberrfp-maroc-db`, and 7 Moroccan procurement sources seeded cleanly.

---

### Task 3: Better Auth Setup & Register / Login / Logout Endpoints

**Files:**
- Create: `backend-next/src/lib/auth.ts`
- Create: `backend-next/src/lib/auth-helpers.ts`
- Create: `backend-next/src/app/api/auth/[...all]/route.ts`
- Create: `backend-next/src/app/api/auth/register/route.ts`
- Create: `backend-next/src/app/api/auth/login/route.ts`
- Create: `backend-next/src/app/api/auth/logout/route.ts`
- Test: `backend-next/tests/auth-routes.test.ts`

**Interfaces:**
- Consumes: `getDb()`, `user`, `session` from `src/db/*`; `getEnv()`, `isEmailDomainAllowed()` from `src/lib/env.ts`; `apiSuccess`, `apiError`, `parseJsonBody`, `toSafeUser` from `src/lib/http.ts`.
- Produces:
  - `getAuth()` in `src/lib/auth.ts`
  - `getAuthenticatedSession(request: NextRequest)` and `requireAuthenticatedUser(request: NextRequest)` in `src/lib/auth-helpers.ts`
  - Route handlers for `/api/auth/[...all]`, `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`.

- [ ] **Step 1: Inspect `node_modules/better-auth` exports for `bearer()` and `nextCookies()`, then write failing tests**

In `backend-next/tests/auth-routes.test.ts`:
- `test_register_validates_payload_and_rejects_role_escalation`: passing `role: 'admin'` or unknown keys or short password returns `400 VALIDATION_ERROR`.
- `test_register_enforces_allowed_email_domains_when_configured`: non-allowlisted domain returns `403 FORBIDDEN`.
- `test_register_creates_user_with_analyst_role_and_returns_token_and_cookie`: returns `201`, `user.role === 'analyst'`, `user.fullName`, `token` non-empty, no `password` field, and `409 CONFLICT` on duplicate email.
- `test_login_returns_safe_user_and_bearer_token_or_401_on_bad_credentials`: valid login returns `200` with `{ user, token }` and `Set-Cookie`; invalid password returns `401 UNAUTHORIZED`.
- `test_logout_revokes_session_and_clears_cookie`: calls Better Auth signOut with request headers and forwards clearing headers (`200 { status: 'ok' }`).

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/auth-routes.test.ts`
Expected: FAIL because `src/lib/auth.ts` and auth routes do not exist yet.

- [ ] **Step 3: Implement `src/lib/auth.ts`, `src/lib/auth-helpers.ts`, and all `/api/auth/*` routes**

- Configure Better Auth lazily in `getAuth()` with `drizzleAdapter(getDb(), { provider: 'pg', schema })`, `emailAndPassword: { enabled: true, minPasswordLength: 8 }`, `user.additionalFields` (`role` default `'analyst'` `input: false`, `jobTitle`, `company`, `whatsappPhone`, `whatsappAlertsEnabled`, `emailAlertsEnabled`, `preferredLanguage`), `plugins: [bearer(), nextCookies()]` (`nextCookies()` last), `trustedOrigins`, and `cookieCache`.
- In `/api/auth/register` and `/api/auth/login`, use Zod `.strict()` schemas, forward `Set-Cookie` headers from `auth.api.*({ ..., returnHeaders: true })` (or `asResponse: true`), extract the session Bearer token cleanly, and return `{ user: SafeUser, token }`.
- In `src/lib/auth-helpers.ts`, `getAuthenticatedSession(request)` calls `getAuth().api.getSession({ headers: request.headers })` (which supports both `Authorization: Bearer` and cookies) and fetches the full `user` row by `session.user.id`.

- [ ] **Step 4: Run tests and TypeScript check to verify Task 3 passes**

Run: `npx vitest run tests/auth-routes.test.ts && npx tsc --noEmit`
Expected: PASS.

---

### Task 4: Profile API (`GET/PATCH /api/profile`), BOLA/IDOR Tests, `next build` & Live Neon Verification

**Files:**
- Create: `backend-next/src/app/api/profile/route.ts`
- Test: `backend-next/tests/profile-routes.test.ts`

**Interfaces:**
- Consumes: `requireAuthenticatedUser(request)` from `src/lib/auth-helpers.ts`, `getDb()` & `user` from `src/db/*`, `apiSuccess`, `apiError`, `parseJsonBody`, `toSafeUser` from `src/lib/http.ts`.
- Produces: `GET /api/profile` and `PATCH /api/profile` route handlers.

- [ ] **Step 1: Write failing tests for `GET /api/profile` and `PATCH /api/profile`**

In `backend-next/tests/profile-routes.test.ts`:
- `test_profile_requires_authentication`: `GET /api/profile` and `PATCH /api/profile` without valid Bearer/cookie return `401 UNAUTHORIZED`.
- `test_get_profile_returns_only_authenticated_user`: User A gets only User A's `SafeUser`, even if `?userId=userB` query param is supplied (BOLA/IDOR check).
- `test_patch_profile_updates_allowlisted_fields_and_e164_phone`: updates `fullName`, `jobTitle`, `company`, `whatsappPhone` (`+212612345678`), `whatsappAlertsEnabled`, `emailAlertsEnabled`, `preferredLanguage`; allows `whatsappPhone: null`.
- `test_patch_profile_rejects_invalid_phone_and_privilege_escalation`: invalid phone (`0612345678`) or attempting `role: 'admin'` or `id: 'userB'` returns `400 VALIDATION_ERROR`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/profile-routes.test.ts`
Expected: FAIL because `src/app/api/profile/route.ts` does not exist yet.

- [ ] **Step 3: Implement `src/app/api/profile/route.ts`**

- `GET`: calls `requireAuthenticatedUser(request)`, returns `apiSuccess({ user: toSafeUser(userRow) })`.
- `PATCH`: calls `requireAuthenticatedUser(request)`, validates strict Zod body (`fullName?`, `jobTitle?`, `company?`, `whatsappPhone?` matching `^\+[1-9]\d{6,14}$` or `null`, `whatsappAlertsEnabled?`, `emailAlertsEnabled?`, `preferredLanguage?`), updates `user` strictly `where(eq(user.id, authUser.id))`, returns updated `{ user: SafeUser }`.

- [ ] **Step 4: Run full Vitest suite, `next build` (even with empty build env), and live end-to-end verification against Neon Postgres**

Run:
1. `npx vitest run` (all unit/integration tests pass)
2. `npx tsc --noEmit`
3. `npm run build` (Next.js production build succeeds cleanly)
4. Live verification script against local `next start` / `next dev` + real Neon Postgres (`cyberrfp-maroc-db`):
   - `GET /api/health` -> `200` with `database: "connected"`
   - `GET /api/auth/ok` -> `200 { status: "ok" }`
   - `POST /api/auth/register` -> `201` with `token` and `role: "analyst"`
   - `GET /api/profile` with `Authorization: Bearer <token>` -> `200` matching registered user
   - `PATCH /api/profile` with `whatsappPhone: "+212600000001", whatsappAlertsEnabled: true` -> `200` persisted in Postgres
   - `POST /api/auth/logout` -> `200`, then `GET /api/profile` with revoked token -> `401 UNAUTHORIZED`
   - Clean up the temporary test user from Neon Postgres afterward.
