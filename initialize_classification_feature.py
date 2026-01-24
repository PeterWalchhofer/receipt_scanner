#!/usr/bin/env python
"""
Database initialization script for the product classification feature.
Run this once to set up the new tables and schema changes.

Usage:
    python initialize_classification_feature.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.update_schema import (
    create_sortiment_table,
    create_regex_table,
    add_product_class_reference,
)

DB_PATH = "receipts.db"


def initialize_database():
    """Initialize all tables and schema changes for the classification feature."""
    print("🔄 Initializing product classification feature...")
    
    try:
        print("\n1️⃣  Creating sortiment table...")
        create_sortiment_table(DB_PATH)
        print("   ✅ Sortiment table ready")
        
        print("\n2️⃣  Creating regex table...")
        create_regex_table(DB_PATH)
        print("   ✅ Regex table ready")
        
        print("\n3️⃣  Adding product_class_reference column...")
        add_product_class_reference(DB_PATH)
        print("   ✅ Product classification column added")
        
        print("\n✨ Database initialization complete!")
        print("\nNext steps:")
        print("  1. Start the Streamlit app: streamlit run app.py")
        print("  2. Visit 📦 Sortiment Management to create product classes")
        print("  3. Visit 🔗 Product Reference Tool to set up regex patterns")
        print("  4. Use batch assign to classify your products")
        print("  5. View aggregations in Käseinnahmen page")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    initialize_database()
