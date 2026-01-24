#!/usr/bin/env python
"""
Script to identify and remove orphaned products (products without corresponding receipts).
Also adds database constraint to prevent this in the future.

Usage:
    python scripts/cleanup_orphaned_products.py [--fix]
    
    Without --fix: Only shows orphaned products (dry-run)
    With --fix: Removes orphaned products and adds constraint
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from repository.receipt_repository import SessionLocal, ProductDB, ReceiptDB


def find_orphaned_products():
    """Find all products that don't have a corresponding receipt."""
    with SessionLocal() as session:
        # Find products where receipt_id doesn't exist in receipts table
        orphaned = session.query(ProductDB).filter(
            ~ProductDB.receipt_id.in_(
                session.query(ReceiptDB.id)
            )
        ).all()
        return orphaned


def count_orphaned_products():
    """Count orphaned products."""
    orphaned = find_orphaned_products()
    return len(orphaned)


def remove_orphaned_products():
    """Remove all orphaned products from the database."""
    orphaned = find_orphaned_products()
    
    if not orphaned:
        print("✅ No orphaned products found!")
        return 0
    
    count = len(orphaned)
    with SessionLocal() as session:
        for product in orphaned:
            session.delete(product)
        session.commit()
    
    return count


def add_cascade_delete_constraint(db_path="receipts.db"):
    """
    Add ON DELETE CASCADE constraint to prevent orphaned products.
    Note: SQLite doesn't support modifying foreign keys directly,
    so we need to recreate the table with the proper constraint.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # First disable and enable foreign keys to ensure clean slate
        cur.execute("PRAGMA foreign_keys=OFF;")
        
        # Check if the constraint already has CASCADE by querying the table info
        cur.execute("PRAGMA foreign_key_list(products);")
        fk_info = cur.fetchall()
        
        has_cascade = any(row[5] == 'CASCADE' for row in fk_info if row[3] == 'receipts')
        
        if has_cascade:
            print("✅ ON DELETE CASCADE constraint already exists")
            cur.execute("PRAGMA foreign_keys=ON;")
            return True
        
        # Rename the old products table
        cur.execute("ALTER TABLE products RENAME TO products_old;")
        
        # Create new products table with ON DELETE CASCADE
        cur.execute("""
            CREATE TABLE products (
                id TEXT PRIMARY KEY,
                receipt_id TEXT NOT NULL,
                name TEXT,
                is_bio BOOLEAN,
                bio_category TEXT,
                amount FLOAT,
                price FLOAT,
                unit TEXT,
                product_class_reference TEXT,
                created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
                FOREIGN KEY (product_class_reference) REFERENCES sortiment(id) ON DELETE SET NULL
            );
        """)
        
        # Copy data from old table to new table
        cur.execute("""
            INSERT INTO products 
            SELECT * FROM products_old;
        """)
        
        # Drop the old table
        cur.execute("DROP TABLE products_old;")
        
        # Recreate indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_products_receipt_id 
            ON products(receipt_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_products_product_class_reference 
            ON products(product_class_reference);
        """)
        
        conn.commit()
        cur.execute("PRAGMA foreign_keys=ON;")
        print("✅ Added ON DELETE CASCADE constraint to products table")
        return True
        
    except Exception as e:
        print(f"❌ Error adding constraint: {e}")
        conn.rollback()
        cur.execute("PRAGMA foreign_keys=ON;")
        return False
    finally:
        conn.close()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("🔄 Cleaning up orphaned products...")
        print()
        
        # First, check current state
        count = count_orphaned_products()
        
        if count == 0:
            print("✅ No orphaned products found!")
        else:
            print(f"⚠️  Found {count} orphaned product(s)")
            orphaned = find_orphaned_products()
            for p in orphaned:
                print(f"   - Product: {p.name} (ID: {p.id}, Receipt ID: {p.receipt_id})")
            print()
            
            # Remove them
            removed = remove_orphaned_products()
            print(f"✅ Removed {removed} orphaned product(s)")
        
        print()
        print("🔐 Adding CASCADE DELETE constraint to prevent future orphans...")
        if add_cascade_delete_constraint():
            print("✅ Constraint added successfully!")
        else:
            print("⚠️  Could not add constraint (it may already exist)")
        
        print()
        print("✨ Cleanup complete!")
        
    else:
        # Dry run - just show what would be deleted
        count = count_orphaned_products()
        
        if count == 0:
            print("✅ No orphaned products found!")
        else:
            print(f"⚠️  Found {count} orphaned product(s) that would be deleted:")
            print()
            orphaned = find_orphaned_products()
            for i, p in enumerate(orphaned, 1):
                print(f"{i}. Product: {p.name}")
                print(f"   ID: {p.id}")
                print(f"   Receipt ID: {p.receipt_id} (DOES NOT EXIST)")
                print()
            
            print("Run with --fix flag to remove these products and add constraint:")
            print("  python scripts/cleanup_orphaned_products.py --fix")


if __name__ == "__main__":
    main()
