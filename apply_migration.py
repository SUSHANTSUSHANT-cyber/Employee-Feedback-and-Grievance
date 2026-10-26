#!/usr/bin/env python3
"""
Apply employeeCodeRequired migration to the database
Run from project root: python apply_migration.py
"""

import sys
import os
from pathlib import Path

# Read .env file
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Get database connection parameters
from urllib.parse import quote_plus

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'employee_assistant')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

# URL-encode the password to handle special characters
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print("Applying employeeCodeRequired migration...")
print("=" * 60)
print(f"Database: {POSTGRES_DB}")
print(f"Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
print("=" * 60)

try:
    from sqlalchemy import create_engine, text
    
    engine = create_engine(DATABASE_URL)
    
    # Read migration file
    migration_sql = Path('database/migrations/20261005_category_employee_code_required.sql').read_text()
    
    print("\nExecuting migration SQL...")
    
    with engine.connect() as conn:
        # Execute the migration
        conn.execute(text(migration_sql))
        conn.commit()
        
        print("✓ Migration executed successfully")
        
        # Verify the column was added
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'custom_categories'
              AND column_name = 'employeeCodeRequired'
        """))
        
        row = result.fetchone()
        if row:
            print("\n✓ Column verification:")
            print(f"  - Column name: {row[0]}")
            print(f"  - Data type: {row[1]}")
            print(f"  - Nullable: {row[2]}")
            print(f"  - Default: {row[3]}")
        else:
            print("\n✗ Column not found! Migration may have failed.")
            sys.exit(1)
        
        # Check existing categories
        result = conn.execute(text("""
            SELECT name, "employeeCodeRequired"
            FROM custom_categories
            ORDER BY name
        """))
        
        categories = result.fetchall()
        if categories:
            print(f"\n✓ Existing categories ({len(categories)} found):")
            for cat in categories:
                print(f"  - {cat[0]}: employeeCodeRequired = {cat[1]}")
        else:
            print("\n  (No existing categories in database)")
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n✗ Error: SQLAlchemy not installed")
    print(f"  Install with: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nNext steps:")
print("1. Rebuild frontend: cd admin-ui && npm run build")
print("2. Copy build to static: Copy-Item -Recurse -Force admin-ui\\dist\\* api\\static\\")
print("3. Restart API server")
print("4. Test in browser")
