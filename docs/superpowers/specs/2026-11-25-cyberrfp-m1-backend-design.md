# CyberRFP Maroc — Backend & Milestone 1 Design Spec

**Date:** 2026-11-25  
**Scope:** Milestone 1 only — Architecture, PostgreSQL Database, Mobile + Web Authentication, and Core User/Profile API  
**Context:** Existing Python/FastAPI prototype (`CyberRFP Maroc v4.0`) lives in `src/` at the repository root and must remain untouched. The new backend will power an external mobile-first React frontend and future mobile clients, deployed on Vercel.

---

## 1. Intent & Why

Build a clean, production-grade TypeScript backend on Vercel for **CyberRFP Maroc** (Moroccan IT & Cybersecurity public/parapublic tender monitoring) so that:
- An external mobile-first React frontend (and future native/mobile clients) can authenticate users securely across both browsers and mobile devices.
- Core relational data (**users/sessions**, **procurement sources**, and **tenders**) lives in a managed serverless PostgreSQL database ready for Milestones 2–5 (scraping, scheduled jobs, WhatsApp alerts, security hardening, and Vercel deployment).

## 2. Goals, Non-Goals, and Anti-Goals

### Goals (Milestone 1)
1. Initialize a standalone **Next.js 16 (App Router) + TypeScript** backend project in `backend-next/` (Node.js 24/26 LTS Fluid Compute target).
2. Provision and wire a real **Neon PostgreSQL** database via Vercel Marketplace (`@neondatabase/serverless` + **Drizzle ORM** `drizzle-orm/neon-http`), with schema and seed data for Moroccan procurement **sources**, normalized **tenders**, and **users/auth** tables.
3. Implement secure authentication compatible with **both mobile and cross-origin React SPAs (`Authorization: Bearer <token>`)** and **same-origin web clients (HttpOnly session cookies)** using **Better Auth** (`better-auth`) backed by Drizzle/PostgreSQL.
4. Expose validated REST API endpoints with CORS support for the external React frontend:
   - `GET /api/health` — service + database connectivity check
   - `POST /api/auth/register` — user registration (server assigns `role: "analyst"`)
   - `POST /api/auth/login` — credential sign-in returning `{ user, token }` + session cookie
   - `POST /api/auth/logout` — session revocation + cookie clearing
   - `GET /api/profile` — retrieve authenticated user profile & alert preferences
   - `PATCH /api/profile` — update authenticated user profile & alert preferences (`fullName`, `jobTitle`, `company`, `whatsappPhone`, `whatsappAlertsEnabled`, `emailAlertsEnabled`, `preferredLanguage`)
   - `GET|POST /api/auth/[...all]` — Better Auth native handler (session lookup, health `/api/auth/ok`)
5. Provide automated unit/integration tests covering auth flows, Bearer token + cookie verification, input validation, and profile BOLA/IDOR isolation, plus `.env.example` documenting all Milestone 1 variables.

### Non-Goals (Deferred to Milestones 2–5)
- Implementing scrapers (`marchespublics.gov.ma`, Al Barid Bank, SOREC, Atlantic RE, Autoroutes du Maroc, Laprophan, OFPPT) -> **Milestone 2**
- Implementing `vercel-schedules` jobs, tenders search/pagination endpoints, scraper health UI endpoints, or watch-keyword CRUD -> **Milestone 3**
- Implementing Twilio / WhatsApp Cloud alert dispatchers -> **Milestone 4**
- Full API security penetration audit (`api-security`) and production Vercel deployment -> **Milestone 5**
- Modifying or removing the existing Python FastAPI app in `src/`

### Anti-Goals
- Do **not** leave a mock/in-memory database fallback in place of real PostgreSQL.
- Do **not** roll custom password hashing (`crypto`/manual bcrypt) or custom hand-rolled JWT signing (`jsonwebtoken`) when Better Auth provides audited hashing, session rotation, rate limiting, and Bearer token sessions.
- Do **not** initialize database clients at module top-level with eager `neon(process.env.DATABASE_URL!)` calls or JS `Proxy` wrappers (both break Next.js builds or auth adapters). Use a lazy `getDb()` function.

---

## 3. Constraints

- **Workspace coexistence:** `Project One` already contains a Python/FastAPI codebase in `src/`, `tests/`, `docs/`, `.env`. All Milestone 1 backend code goes under `backend-next/` so nothing in `src/` is disturbed.
- **Vercel platform realities:**
  - `@vercel/postgres` and `@vercel/kv` are retired; PostgreSQL must be provisioned via Vercel Marketplace (**Neon** or **Supabase**).
  - Node.js 24/26 LTS on Fluid Compute is the target runtime (no `runtime = 'edge'`).
  - Next.js 16 uses `proxy.ts` (exporting `proxy`) instead of `middleware.ts`.
  - Marketplace integration must be discovered and provisioned via Vercel CLI (`vercel integration discover` -> `vercel integration add neon`) before scaffolding/wiring.
- **Security baseline:** Strict Zod input validation, no `passwordHash` or secrets leaked in API responses, authenticated user identity always derived from verified session/token (never from client-supplied `userId`), server-enforced RBAC `role` (no self-assignment/escalation), and explicit CORS origin allowlist (`ALLOWED_ORIGINS`).

---

## 4. Approaches Considered & Selected Architecture (Our Calls)

### A. Backend Project Location & Framework
- **Selected: `backend-next/` with Next.js 16 (App Router) + TypeScript Route Handlers.**
  - *Why:* Explicitly matches Milestone 1 ("Node.js/Next.js"), deploys with zero config on Vercel Fluid Compute, supports `vercel-schedules` (M3) and `@vercel/functions` seamlessly, and isolates cleanly from the existing Python app in `src/`.
- **Rejected:** Replacing `src/` at repo root (destructive to existing `CyberRFP Maroc v4.0`), or standalone Express/Fastify (misses Next.js App Router + `proxy.ts` ecosystem expected by M1).

### B. PostgreSQL Database & ORM
- **Selected: Neon Postgres via Vercel Marketplace (`@neondatabase/serverless` + Drizzle ORM `drizzle-orm/neon-http`).**
  - *Why:* Vercel's preferred serverless Postgres integration (`vercel integration add neon`), works natively over HTTP on Fluid Compute without TCP connection pool exhaustion, supports Preview DB branching, and avoids redundant Supabase Auth/Realtime layers when Better Auth runs directly in Next.js.
- **Alternative (Deferred/Interchangeable):** Supabase Postgres (because Drizzle uses standard PostgreSQL schemas, switching `DATABASE_URL` later requires zero schema rewrite).

### C. Authentication (Mobile + Cross-Origin Web)
- **Selected (Builder Call): Better Auth (`better-auth`) with Drizzle Postgres adapter, `bearer()` plugin, and `nextCookies()` plugin — dropping `jwt()` / `jwks` in M1.**
  - *Why:*
    1. External React SPAs hosted on a separate `*.vercel.app` origin and mobile apps are cross-site relative to the backend; `SameSite=Lax` cookies are blocked by browsers on cross-site `fetch()`. Using **`Authorization: Bearer <token>`** via Better Auth's `bearer()` plugin as the primary client credential works identically across mobile apps and cross-origin React SPAs without third-party cookie failures.
    2. Better Auth `bearer()` issues opaque session tokens stored in PostgreSQL `session` and verified via `auth.api.getSession({ headers })`. Unlike stateless JWTs, **`POST /api/auth/logout` revokes tokens immediately** in PostgreSQL.
    3. `SameSite=Lax` HttpOnly cookies are still emitted on login/register for same-origin web usage (e.g., if the frontend is later proxied under one domain via Vercel rewrites).
    4. Built-in scrypt password hashing, session expiry/rotation, and Drizzle schema generation avoid fragile custom auth code.
- **Rejected:** Auth.js / NextAuth (cookie-centric, awkward for mobile Bearer REST endpoints), `jwt()` stateless tokens in M1 (cannot be revoked on `/logout` and no external consumer needs JWKS in M1), custom `jsonwebtoken` + `bcryptjs`.

### D. Authorization (`role` vs `jobTitle`) & Registration Policy
- **Selected (Builder Call):**
  - `role` is strictly an **RBAC authorization enum** (`"analyst" | "admin"`), defaulting to `"analyst"`. Public `POST /api/auth/register` and `PATCH /api/profile` **never accept or modify `role`** (`input: false` in Better Auth config + Zod allowlist). Admin elevation happens only via DB/seed or future admin endpoints.
  - `jobTitle` (nullable text) stores the user's editable professional title (e.g. `"Consultant Cybersécurité"`).
  - Registration email domain policy is controlled by an optional **`ALLOWED_EMAIL_DOMAINS`** env var (empty/unset = open registration; comma-separated e.g. `dpg-cyber.com` = domain-restricted).

---

## 5. Detailed Design (Milestone 1)

### 5.1 Directory Structure (`backend-next/`)
```text
backend-next/
├── drizzle.config.ts
├── next.config.ts
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── .env.example
└── src/
    ├── proxy.ts                         # CORS allowlist + security headers for /api/*
    ├── db/
    │   ├── index.ts                     # Lazy getDb() using neon() + drizzle (no Proxy)
    │   ├── schema.ts                    # user, session, account, verification, sources, tenders
    │   └── seed.ts                      # Idempotent seed for the 7 Moroccan procurement sources
    ├── lib/
    │   ├── auth.ts                      # Lazy getAuth() configuring Better Auth + bearer + Drizzle
    │   ├── auth-helpers.ts              # Unified request session resolver (Bearer header OR Cookie)
    │   ├── env.ts                       # Validated runtime env accessors
    │   └── http.ts                      # Standard SafeUser mapper, JSON responses & error envelopes
    └── app/
        └── api/
            ├── health/route.ts          # GET: DB ping + service status
            ├── auth/
            │   ├── [...all]/route.ts    # GET/POST: Better Auth native routes (/ok, /get-session)
            │   ├── register/route.ts    # POST: register + return { user, token } + cookie
            │   ├── login/route.ts       # POST: login + return { user, token } + cookie
            │   └── logout/route.ts      # POST: revoke session + clear cookie
            └── profile/route.ts         # GET/PATCH: authenticated user profile & alert prefs
```

### 5.2 Database Schema (`src/db/schema.ts`)
1. **Better Auth User & Auth Tables:**
   - `user`:
     - `id` (text PK)
     - `name` (text, not null — mapped to `fullName` in API responses/requests)
     - `email` (text, unique, not null)
     - `emailVerified` (boolean, not null, default `false`)
     - `image` (text, nullable)
     - `role` (text, not null, default `'analyst'` — RBAC: `'analyst' | 'admin'`, `input: false` on sign-up)
     - `jobTitle` (text, nullable — editable profile title)
     - `company` (text, nullable)
     - `whatsappPhone` (text, nullable — E.164 validated at API layer)
     - `whatsappAlertsEnabled` (boolean, not null, default `false`)
     - `emailAlertsEnabled` (boolean, not null, default `true`)
     - `preferredLanguage` (text, not null, default `'fr'` — `'fr' | 'en' | 'ar'`)
     - `createdAt` (timestamp, not null, defaultNow)
     - `updatedAt` (timestamp, not null, defaultNow)
   - `session`: `id` (text PK), `expiresAt` (timestamp not null), `token` (text unique not null), `ipAddress` (text), `userAgent` (text), `userId` (text FK -> `user.id` cascade), `createdAt` (timestamp not null), `updatedAt` (timestamp not null).
   - `account`: `id` (text PK), `accountId` (text not null), `providerId` (text not null), `userId` (text FK -> `user.id` cascade), `accessToken`, `refreshToken`, `idToken`, `accessTokenExpiresAt`, `refreshTokenExpiresAt`, `scope`, `password`, `createdAt`, `updatedAt`.
   - `verification`: `id` (text PK), `identifier` (text not null), `value` (text not null), `expiresAt` (timestamp not null), `createdAt`, `updatedAt`.
2. **`sources` Table:**
   - `id` (uuid PK defaultRandom), `slug` (text unique not null), `name` (text not null), `baseUrl` (text not null), `scraperType` (text not null — `'pmmp' | 'al_barid_bank' | 'sorec' | 'atlantic_re' | 'adm' | 'laprophan' | 'ofppt'`), `isActive` (boolean not null default `true`), `healthStatus` (text not null default `'pending'`), `lastRunAt` (timestamp nullable), `lastSuccessAt` (timestamp nullable), `lastError` (text nullable), `itemsIndexed` (integer not null default `0`), `createdAt` (timestamp not null defaultNow), `updatedAt` (timestamp not null defaultNow).
   - **Initial idempotent seed (`src/db/seed.ts`):**
     - `pmmp` (`https://www.marchespublics.gov.ma`)
     - `al-barid-bank` (`https://fournisseurs.albaridbank.ma`)
     - `sorec` (`https://www.sorec.ma/appels-offres/`)
     - `atlantic-re` (`https://www.atlanticre.ma`)
     - `autoroutes-du-maroc` (`https://www.adm.co.ma`)
     - `laprophan` (`https://www.laprophan.com`)
     - `ofppt` (`https://www.ofppt.ma`)
3. **`tenders` Table (normalized core ready for M2–M4):**
   - `id` (uuid PK defaultRandom), `dedupHash` (text unique not null), `sourceId` (uuid FK -> `sources.id` onDelete restrict), `externalRef` (text nullable), `title` (text not null), `clientName` (text not null), `clientNormalized` (text nullable), `category` (text nullable), `publicationDate` (timestamp nullable), `deadline` (timestamp nullable), `directUrl` (text not null), `status` (text not null default `'open'`), `isHighPriority` (boolean not null default `false`), `matchedKeywords` (jsonb `string[]` not null default `[]`), `relevanceScore` (integer not null default `0`), `rawMetadata` (jsonb nullable), `createdAt` (timestamp not null defaultNow), `updatedAt` (timestamp not null defaultNow).
   - Indexes on `tenders(sourceId)`, `tenders(status, deadline)`, and `tenders(isHighPriority, createdAt)`.

### 5.3 API Contract (`SafeUser`, Error Envelopes & Endpoints)

- **`SafeUser` JSON Shape (returned by `/register`, `/login`, `GET /profile`, `PATCH /profile`):**
  ```ts
  type SafeUser = {
    id: string;
    email: string;
    fullName: string;              // backed by user.name
    role: "analyst" | "admin";
    jobTitle: string | null;
    company: string | null;
    whatsappPhone: string | null;
    whatsappAlertsEnabled: boolean;
    emailAlertsEnabled: boolean;
    preferredLanguage: "fr" | "en" | "ar";
    createdAt: string;             // ISO 8601
    updatedAt: string;             // ISO 8601
  };
  ```
- **Standard Error Envelope:**
  ```ts
  {
    error: {
      code: "VALIDATION_ERROR" | "UNAUTHORIZED" | "FORBIDDEN" | "CONFLICT" | "INTERNAL_ERROR";
      message: string;
      details?: Record<string, string[]>; // Zod fieldErrors on 400
    }
  }
  ```
- **Session Resolution (`getAuthenticatedSession(request)`):**
  - Calls `getAuth().api.getSession({ headers: request.headers })`.
  - Better Auth's `bearer()` plugin transparently accepts `Authorization: Bearer <token>` (for mobile & cross-origin SPAs) AND session cookies (for same-origin web).
  - Returns `null` when missing/invalid/expired -> endpoints respond `401` with `code: "UNAUTHORIZED"`.
- **Endpoints:**
  - `GET /api/health`: Runs `SELECT 1` against Postgres; returns `200 { status: "ok", database: "connected", timestamp }` or `503` on DB failure.
  - `POST /api/auth/register`:
    - Body (Zod): `{ email, password (min 8 chars), fullName (min 2 chars), jobTitle?, company?, whatsappPhone? (E.164 `^\+[1-9]\d{6,14}$`), preferredLanguage? ('fr'|'en'|'ar') }`.
    - Rejects unknown fields or disallowed email domain (when `ALLOWED_EMAIL_DOMAINS` is set, returns `403 FORBIDDEN`).
    - Calls `auth.api.signUpEmail` (returning full response headers/cookies + token), updates optional profile fields (`jobTitle`, `company`, `whatsappPhone`, `preferredLanguage`), returns `201 Created` `{ user: SafeUser, token }` + Better Auth `Set-Cookie` headers. Duplicate email -> `409 CONFLICT`.
  - `POST /api/auth/login`:
    - Body (Zod): `{ email, password }`.
    - Calls `auth.api.signInEmail`, queries full `SafeUser` row, returns `200 OK` `{ user: SafeUser, token }` + Better Auth `Set-Cookie` headers. Invalid credentials -> `401 UNAUTHORIZED`.
  - `POST /api/auth/logout`:
    - Calls `auth.api.signOut({ headers: request.headers })` (revoking Bearer/cookie session in DB) and clears session cookie (`200 OK { status: "ok" }`).
  - `GET /api/profile`:
    - Requires valid session/Bearer token. Queries `user` strictly by `session.user.id` -> `200 OK { user: SafeUser }`.
  - `PATCH /api/profile`:
    - Requires valid session/Bearer token.
    - Body (Zod strict allowlist — **never** accepts `id`, `email`, `role`, `emailVerified`, `createdAt`): `{ fullName?, jobTitle?, company?, whatsappPhone? (E.164 or null), whatsappAlertsEnabled?, emailAlertsEnabled?, preferredLanguage? ('fr'|'en'|'ar') }`.
    - Updates `where(eq(user.id, session.user.id))` and returns `200 OK { user: SafeUser }`.
- **CORS (`src/proxy.ts`):**
  - Reads `ALLOWED_ORIGINS` (comma-separated, e.g., `http://localhost:5173,http://localhost:3000`).
  - Returns dynamic `Access-Control-Allow-Origin` matching the request `Origin` when in `ALLOWED_ORIGINS` (never `*` with credentials), `Access-Control-Allow-Methods: GET, POST, PATCH, PUT, DELETE, OPTIONS`, `Access-Control-Allow-Headers: Content-Type, Authorization`, `Access-Control-Allow-Credentials: true`, and `Vary: Origin`.
  - Adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 6. Left to the Builder / Implementation Plan

- Exact Better Auth v1.x `bearer()` plugin import path and `signUpEmail` / `signInEmail` response-token extraction verified directly against installed `node_modules/better-auth` types during Milestone 1 setup.
- Vitest test suite setup with mocked/test Postgres and end-to-end verification against the provisioned Neon PostgreSQL database via Vercel Marketplace.
- `BETTER_AUTH_SECRET` generation and Vercel environment variable sync (`vercel env add` / `vercel env pull`).
