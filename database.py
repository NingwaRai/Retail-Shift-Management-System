import sqlite3


DATABASE = "retail_shift_management.db"


def connect():
    return sqlite3.connect(DATABASE)


def create_tables():

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees(

        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,

        first_name TEXT NOT NULL,

        last_name TEXT NOT NULL,

        phone TEXT,

        email TEXT,

        position TEXT

    )
    """)


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