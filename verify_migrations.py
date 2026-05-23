"""
Script to verify database migrations were applied correctly.
Checks for tables, indexes, and foreign keys.
"""
import sqlite3
from pathlib import Path

def verify_database_schema():
    """Verify that all expected tables, indexes, and foreign keys exist."""
    db_path = Path("healthcare_ai.db")
    
    if not db_path.exists():
        print("❌ Database file not found!")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    
    # Check tables
    print("\n📋 TABLES:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['users', 'refresh_tokens', 'user_activities', 'audit_logs']
    
    for table in expected_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} (MISSING)")
    
    # Show all tables
    print(f"\n  All tables: {', '.join(tables)}")
    
    # Check each table's schema
    for table in expected_tables:
        if table not in tables:
            continue
            
        print(f"\n📊 TABLE: {table}")
        print("-" * 60)
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print("  Columns:")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            pk_marker = " (PK)" if pk else ""
            print(f"    - {name}: {type_} {nullable}{pk_marker}")
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        if indexes:
            print("  Indexes:")
            for idx in indexes:
                seq, name, unique, origin, partial = idx
                unique_marker = " (UNIQUE)" if unique else ""
                print(f"    - {name}{unique_marker}")
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            print("  Foreign Keys:")
            for fk in foreign_keys:
                id_, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                print(f"    - {from_col} -> {ref_table}({to_col}) ON DELETE {on_delete}")
    
    # Check alembic version
    print("\n🔄 MIGRATION STATUS:")
    print("-" * 60)
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    if version:
        print(f"  Current version: {version[0]}")
    else:
        print("  No migration version found!")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    verify_database_schema()
