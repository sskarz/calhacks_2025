import sqlite3

# Initializers 
def get_db_connection(db_path='database.db'):
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary-like row access
        return conn
    except sqlite3.OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

def initialize_db(conn):
    """Initializes the database with a sample table."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class TEXT NOT NULL,
                init_price REAL NOT NULL,
                high_price REAL NOT NULL DEFAULT init_price,
                status TEXT DEFAULT 'available' CHECK (status IN ('available', 'sold', 'pending'))
            )
        ''')
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# Modifiers

def add_item(item_class, init_price, conn):
    """Adds a new item to the database."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (class, init_price) VALUES (?, ?)
        ''', (item_class, init_price))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error adding item: {e}")
    finally:
        conn.close()

def update_high_price(item_id, asking_price, conn):
    """Updates the high price of an item if asking_price is higher.
    
    Returns:
        (True, asking_price) if price was updated
        (False, current_high_price) if price was not updated
    """
    try:
        cursor = conn.cursor()
        result = cursor.execute('''
            SELECT high_price FROM users WHERE id = ?
        ''', (item_id,))
        
        current_high = result.fetchone()['high_price']
        
        if current_high < asking_price:
            cursor.execute('''
                UPDATE users SET high_price = ? WHERE id = ?
            ''', (asking_price, item_id))
            conn.commit()
            return (True, asking_price)
        
        return (False, current_high)
    except (sqlite3.OperationalError, TypeError) as e:
        print(f"Error updating high price: {e}")
        return None
    finally:
        conn.close()

def update_status(item_id, new_status, conn):
    """Updates the status of an item."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET status = ? WHERE id = ?
        ''', (new_status, item_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error updating status: {e}")
    except sqlite3.OperationalError as e:
        print(f"Database error updating status: {e}")
    finally:
        conn.close()

# Retrievers
def get_all_items(conn):
    """Retrieves all items from the database."""
    try:
        cursor = conn.cursor()
        result = cursor.execute('SELECT * FROM users')
        items = result.fetchall()
        return items
    except sqlite3.OperationalError as e:
        print(f"Error retrieving items: {e}")
        return None
    finally:
        conn.close()

def get_item_by_id(item_id, conn):
    """Retrieves a specific item by its ID."""
    try:
        cursor = conn.cursor()
        result = cursor.execute('SELECT * FROM users WHERE id = ?', (item_id,))
        item = result.fetchone()
        return item
    except sqlite3.OperationalError as e:
        print(f"Error retrieving item: {e}")
        return None
    finally:
        conn.close()

def check_state(item_id, conn):
    """Checks the status of a specific item."""
    try:
        cursor = conn.cursor()
        result = cursor.execute('SELECT status FROM users WHERE id = ?', (item_id,))
        status_row = result.fetchone()
        return status_row['status'] if status_row else None
    except (sqlite3.OperationalError, TypeError) as e:
        print(f"Error checking status: {e}")
        return None
    finally:
        conn.close()