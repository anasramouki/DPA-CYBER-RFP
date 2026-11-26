import {
  pgTable,
  text,
  timestamp,
  boolean,
  uuid,
  integer,
  jsonb,
  index,
} from 'drizzle-orm/pg-core';
import type { InferSelectModel, InferInsertModel } from 'drizzle-orm';

// --- Better Auth Core Tables ---

export const user = pgTable('user', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  emailVerified: boolean('email_verified').notNull().default(false),
  image: text('image'),
  role: text('role').notNull().default('analyst'),
  jobTitle: text('job_title'),
  company: text('company'),
  whatsappPhone: text('whatsapp_phone'),
  whatsappAlertsEnabled: boolean('whatsapp_alerts_enabled').notNull().default(false),
  emailAlertsEnabled: boolean('email_alerts_enabled').notNull().default(true),
  preferredLanguage: text('preferred_language').notNull().default('fr'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
});

export const session = pgTable(
  'session',
  {
    id: text('id').primaryKey(),
    expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
    token: text('token').notNull().unique(),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
    ipAddress: text('ip_address'),
    userAgent: text('user_agent'),
    userId: text('user_id')
      .notNull()
      .references(() => user.id, { onDelete: 'cascade' }),
  },
  (table) => [index('session_user_id_idx').on(table.userId)]
);

export const account = pgTable(
  'account',
  {
    id: text('id').primaryKey(),
    accountId: text('account_id').notNull(),
    providerId: text('provider_id').notNull(),
    userId: text('user_id')
      .notNull()
      .references(() => user.id, { onDelete: 'cascade' }),
    accessToken: text('access_token'),
    refreshToken: text('refresh_token'),
    idToken: text('id_token'),
    accessTokenExpiresAt: timestamp('access_token_expires_at', { withTimezone: true }),
    refreshTokenExpiresAt: timestamp('refresh_token_expires_at', { withTimezone: true }),
    scope: text('scope'),
    password: text('password'),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index('account_user_id_idx').on(table.userId)]
);

export const verification = pgTable(
  'verification',
  {
    id: text('id').primaryKey(),
    identifier: text('identifier').notNull(),
    value: text('value').notNull(),
    expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index('verification_identifier_idx').on(table.identifier)]
);

// --- Domain Tables (CyberRFP Maroc) ---

export const sources = pgTable('sources', {
  id: uuid('id').defaultRandom().primaryKey(),
  slug: text('slug').notNull().unique(),
  name: text('name').notNull(),
  baseUrl: text('base_url').notNull(),
  scraperType: text('scraper_type').notNull(),
  isActive: boolean('is_active').notNull().default(true),
  healthStatus: text('health_status').notNull().default('pending'),
  lastRunAt: timestamp('last_run_at', { withTimezone: true }),
  lastSuccessAt: timestamp('last_success_at', { withTimezone: true }),
  lastError: text('last_error'),
  itemsIndexed: integer('items_indexed').notNull().default(0),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
});

export const tenders = pgTable(
  'tenders',
  {
    id: uuid('id').defaultRandom().primaryKey(),
    dedupHash: text('dedup_hash').notNull().unique(),
    sourceId: uuid('source_id')
      .notNull()
      .references(() => sources.id, { onDelete: 'restrict' }),
    externalRef: text('external_ref'),
    title: text('title').notNull(),
    clientName: text('client_name').notNull(),
    clientNormalized: text('client_normalized'),
    category: text('category'),
    publicationDate: timestamp('publication_date', { withTimezone: true }),
    deadline: timestamp('deadline', { withTimezone: true }),
    directUrl: text('direct_url').notNull(),
    status: text('status').notNull().default('open'),
    isHighPriority: boolean('is_high_priority').notNull().default(false),
    matchedKeywords: jsonb('matched_keywords').$type<string[]>().notNull().default([]),
    relevanceScore: integer('relevance_score').notNull().default(0),
    rawMetadata: jsonb('raw_metadata').$type<Record<string, unknown> | null>(),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [
    index('tenders_source_id_idx').on(table.sourceId),
    index('tenders_status_deadline_idx').on(table.status, table.deadline),
    index('tenders_priority_created_idx').on(table.isHighPriority, table.createdAt),
  ]
);

export const watchlist = pgTable(
  'watchlist',
  {
    id: uuid('id').defaultRandom().primaryKey(),
    userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }),
    keyword: text('keyword').notNull(),
    category: text('category').default('cyber'),
    isActive: boolean('is_active').notNull().default(true),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index('watchlist_user_id_idx').on(table.userId)]
);

export type UserRow = InferSelectModel<typeof user>;
export type NewUserRow = InferInsertModel<typeof user>;

export type SessionRow = InferSelectModel<typeof session>;
export type NewSessionRow = InferInsertModel<typeof session>;

export type AccountRow = InferSelectModel<typeof account>;
export type NewAccountRow = InferInsertModel<typeof account>;

export type VerificationRow = InferSelectModel<typeof verification>;
export type NewVerificationRow = InferInsertModel<typeof verification>;

export type SourceRow = InferSelectModel<typeof sources>;
export type NewSourceRow = InferInsertModel<typeof sources>;

export type TenderRow = InferSelectModel<typeof tenders>;
export type NewTenderRow = InferInsertModel<typeof tenders>;

export type WatchlistRow = InferSelectModel<typeof watchlist>;
export type NewWatchlistRow = InferInsertModel<typeof watchlist>;
