import sqlite3


DATABASE = "retail_shift_management.db"


def connect():
    return sqlite3.connect(DATABASE)


def create_tables():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments(
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        required_employees_per_day REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees(

        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,

        first_name TEXT NOT NULL,

        last_name TEXT NOT NULL,

        phone TEXT,

        email TEXT,

        position TEXT,
        
        department_id INTEGER,
        
        FOREIGN KEY(department_id)
        REFERENCES departments(department_id)

    )
    """)

    # Check if department_id column already exists in employees table (for older installations)
    cursor.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cursor.fetchall()]
    if "department_id" not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN department_id INTEGER REFERENCES departments(department_id)")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS availability(

        availability_id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER,

        day_of_week TEXT,

        available TEXT,

        FOREIGN KEY(employee_id)
        REFERENCES employees(employee_id)

    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shifts(

        shift_id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER,

        shift_date TEXT,

        day_of_week TEXT,

        start_time TEXT,

        end_time TEXT,

        position_required TEXT,

        FOREIGN KEY(employee_id)
        REFERENCES employees(employee_id)

    )
    """)


    conn.commit()
    conn.close()