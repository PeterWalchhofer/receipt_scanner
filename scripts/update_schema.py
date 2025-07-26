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



if __name__ == "__main__":
    # add_source_column(DB_PATH)#
    add_products_table(DB_PATH)