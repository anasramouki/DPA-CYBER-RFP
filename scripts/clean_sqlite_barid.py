import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cyberrfp.db")
print(f"Opening {db_path}...")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check initial counts
c.execute("SELECT source_name, count(*) FROM tenders GROUP BY source_name")
print("Before cleanup:", c.fetchall())

# Delete Al Barid Bank tenders
c.execute("DELETE FROM tenders WHERE source_name = 'Al Barid Bank' OR id LIKE 'abb:%' OR lower(buyer_name) LIKE '%barid bank%'")
print(f"Deleted Al Barid Bank tenders: {c.rowcount} rows")

# Keep only PMMP tenders if user asked "laisse seulement ceux du portails des marché public"
# Let's check remaining sources
c.execute("SELECT source_name, count(*) FROM tenders GROUP BY source_name")
print("After removing Al Barid Bank:", c.fetchall())

conn.commit()
conn.close()
print("cyberrfp.db updated successfully.")
