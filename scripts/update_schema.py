import sqlite3
# from repository.receipt_repository import ProductDB

DB_PATH = "receipts.db"  # Change this if your DB file has a different name

def add_source_column(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Add the new column if it doesn't exist
    try:
        cur.execute("ALTER TABLE receipts ADD COLUMN source TEXT;")
        print("Added 'source' column to 'receipts' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'source' column already exists.")
        else:
            raise
    # Set default value for existing rows
    cur.execute("UPDATE receipts SET source = 'RECEIPT_SCANNER' WHERE source IS NULL;")
    conn.commit()
    conn.close()
    print("Set default value for existing rows.")


def add_products_table(db_path):
    # drop products table if it exists
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS products;")
    conn.commit()
    conn.close()


def create_sortiment_table(db_path):
    """Create the sortiment table for product classification."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sortiment (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Created 'sortiment' table.")
    except sqlite3.OperationalError as e:
        print(f"Error creating sortiment table: {e}")
    finally:
        conn.close()


def create_regex_table(db_path):
    """Create the regex table for pattern matching."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS regex (
                id TEXT PRIMARY KEY,
                regex TEXT NOT NULL,
                product_class_id TEXT NOT NULL,
                created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_class_id) REFERENCES sortiment(id)
            )
        """)
        conn.commit()
        print("Created 'regex' table.")
    except sqlite3.OperationalError as e:
        print(f"Error creating regex table: {e}")
    finally:
        conn.close()


def add_product_class_reference(db_path):
    """Add product_class_reference column to products table."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "ALTER TABLE products ADD COLUMN product_class_reference TEXT;"
        )
        print("Added 'product_class_reference' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'product_class_reference' column already exists.")
        else:
            print(f"Error adding product_class_reference column: {e}")
    finally:
        conn.commit()
        conn.close()


if __name__ == "__main__":

    # Uncomment to run migrations
    # add_source_column(DB_PATH)
    # add_products_table(DB_PATH)
    create_sortiment_table(DB_PATH)
    create_regex_table(DB_PATH)
    add_product_class_reference(DB_PATH)
    pass