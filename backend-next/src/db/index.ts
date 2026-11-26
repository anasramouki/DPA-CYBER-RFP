import { neon } from '@neondatabase/serverless';
import { drizzle, NeonHttpDatabase } from 'drizzle-orm/neon-http';
import { sql } from 'drizzle-orm';
import { getDatabaseUrl } from '@/lib/env';
import * as schema from './schema';

export type Database = NeonHttpDatabase<typeof schema>;

let _db: Database | null = null;
let _cachedUrl: string | null = null;

export function getDb(): Database {
  const url = getDatabaseUrl();
  if (_db && _cachedUrl === url) {
    return _db;
  }
  const client = neon(url);
  _db = drizzle(client, { schema });
  _cachedUrl = url;
  return _db;
}

export async function checkDatabaseHealth(): Promise<boolean> {
  try {
    const db = getDb();
    await db.execute(sql`SELECT 1`);
    return true;
  } catch (err) {
    console.error('Database health check failed:', err);
    return false;
  }
}
