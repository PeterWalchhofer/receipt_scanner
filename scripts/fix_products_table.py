#!/usr/bin/env python
"""
Fix the products table after CASCADE DELETE migration issues.

This script fixes:
1. NULL created_on/updated_on timestamps
2. Corrupted product_class_reference (contains dates instead of UUIDs)

Usage:
    python scripts/fix_products_table.py
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = "receipts.db"


def fix_products_table(db_path=DB_PATH):
    """Fix the products table timestamps and references."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        print("🔧 Fixing products table...")
        print()
        
        # Check current state
        cur.execute('SELECT COUNT(*) FROM products;')
        total_products = cur.fetchone()[0]
        print(f"Total products: {total_products}")
        
        # Fix 1: Set updated_on = created_on where updated_on is NULL
        print("\n1️⃣  Fixing updated_on timestamps...")
        cur.execute('''
            UPDATE products 
            SET updated_on = created_on 
            WHERE updated_on IS NULL AND created_on IS NOT NULL;
        ''')
        fixed_updated = cur.rowcount
        print(f"   ✅ Fixed {fixed_updated} products with NULL updated_on")
        
        # Fix 2: Set both created_on and updated_on to current timestamp where both are NULL
        print("\n2️⃣  Fixing missing created_on timestamps...")
        cur.execute('''
            UPDATE products 
            SET created_on = CURRENT_TIMESTAMP, updated_on = CURRENT_TIMESTAMP
            WHERE created_on IS NULL;
        ''')
        fixed_created = cur.rowcount
        print(f"   ✅ Fixed {fixed_created} products with NULL created_on")
        
        # Fix 3: Reset product_class_reference to NULL (corrupted with dates)
        print("\n3️⃣  Clearing corrupted product_class_reference...")
        cur.execute('''
            SELECT COUNT(*) FROM products 
            WHERE product_class_reference IS NOT NULL;
        ''')
        corrupted_count = cur.fetchone()[0]
        
        if corrupted_count > 0:
            cur.execute('UPDATE products SET product_class_reference = NULL;')
            print(f"   ✅ Reset {corrupted_count} corrupted product_class_reference values to NULL")
        else:
            print(f"   ✅ No corrupted references found")
        
        conn.commit()
        
        # Verify fixes
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        
        cur.execute('SELECT COUNT(*) FROM products WHERE created_on IS NULL;')
        null_created = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM products WHERE updated_on IS NULL;')
        null_updated = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM products WHERE product_class_reference IS NOT NULL;')
        remaining_refs = cur.fetchone()[0]
        
        print(f"\nProducts with NULL created_on: {null_created}")
        print(f"Products with NULL updated_on: {null_updated}")
        print(f"Products with non-NULL product_class_reference: {remaining_refs}")
        
        if null_created == 0 and null_updated == 0 and remaining_refs == 0:
            print("\n✨ All fixes applied successfully!")
            return True
        else:
            print("\n⚠️  Some issues remain - check the counts above")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = fix_products_table()
    sys.exit(0 if success else 1)
