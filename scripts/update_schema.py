import sqlite3

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

if __name__ == "__main__":
    add_source_column(DB_PATH)