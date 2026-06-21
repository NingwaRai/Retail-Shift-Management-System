from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import calendar

from database import create_tables


app = Flask(__name__)


create_tables()


def db():

    conn = sqlite3.connect(
        "retail_shift_management.db"
    )

    conn.row_factory = sqlite3.Row

    return conn



def parse_time_to_float(time_str):
    if not time_str:
        return 0.0
    time_str = time_str.strip()
    for fmt in ('%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M%p'):
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.hour + dt.minute / 60.0
        except ValueError:
            pass
    try:
        parts = time_str.split()
        time_part = parts[0]
        h, m = map(int, time_part.split(':')[:2])
        if len(parts) > 1:
            ampm = parts[1].upper()
            if ampm == 'PM' and h < 12:
                h += 12
            elif ampm == 'AM' and h == 12:
                h = 0
        return h + m / 60.0
    except Exception:
        return 0.0



@app.route("/")
def home():
    conn = db()
    employee_count = conn.execute("SELECT COUNT(*) as count FROM employees").fetchone()["count"]
    shift_count = conn.execute("SELECT COUNT(*) as count FROM shifts").fetchone()["count"]

    # Coverage Dashboard parameters
    dept_id = request.args.get("dept_id")
    view = request.args.get("view", "day")
    date_str = request.args.get("date")

    # Default date to today
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        current_dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        current_dt = datetime.now()
        date_str = current_dt.strftime("%Y-%m-%d")

    # Get all departments to populate filter
    departments_list = conn.execute("SELECT * FROM departments").fetchall()

    # If dept_id is not specified, default to first department, or 'all' if no departments exist
    if not dept_id and departments_list:
        dept_id = str(departments_list[0]["department_id"])
    elif not dept_id:
        dept_id = "all"

    # Navigation parameters
    prev_day = (current_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    next_day = (current_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    # Monday of the current week (weekday() is 0 for Monday)
    start_of_week = current_dt - timedelta(days=current_dt.weekday())
    prev_week = (current_dt - timedelta(weeks=1)).strftime("%Y-%m-%d")
    next_week = (current_dt + timedelta(weeks=1)).strftime("%Y-%m-%d")

    # Month navigation
    if current_dt.month == 1:
        prev_month_dt = datetime(current_dt.year - 1, 12, 1)
    else:
        prev_month_dt = datetime(current_dt.year, current_dt.month - 1, 1)

    if current_dt.month == 12:
        next_month_dt = datetime(current_dt.year + 1, 1, 1)
    else:
        next_month_dt = datetime(current_dt.year, current_dt.month + 1, 1)

    prev_month = prev_month_dt.strftime("%Y-%m-%d")
    next_month = next_month_dt.strftime("%Y-%m-%d")

    coverage_data = {}

    # Determine the date range based on the selected view
    dates_to_calculate = []
    if view == "day":
        dates_to_calculate = [date_str]
    elif view == "week":
        dates_to_calculate = [(start_of_week + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    elif view == "month":
        year = current_dt.year
        month = current_dt.month
        cal = calendar.Calendar(firstweekday=6) # Sunday starts
        month_weeks_days = cal.monthdayscalendar(year, month)
        # Flatten and get non-zero days
        for week in month_weeks_days:
            for day in week:
                if day > 0:
                    dates_to_calculate.append(f"{year}-{month:02d}-{day:02d}")

    # To handle overnight shifts starting on the day before the first date in our calculation:
    if dates_to_calculate:
        first_date_dt = datetime.strptime(dates_to_calculate[0], "%Y-%m-%d")
        min_date_str = (first_date_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        max_date_str = dates_to_calculate[-1]

        # Query shifts for the range
        shifts_query = """
            SELECT shifts.*, employees.first_name, employees.last_name, employees.department_id
            FROM shifts
            JOIN employees ON shifts.employee_id = employees.employee_id
            WHERE shifts.shift_date >= ? AND shifts.shift_date <= ?
        """
        raw_shifts = conn.execute(shifts_query, (min_date_str, max_date_str)).fetchall()

        # Calculate coverage details
        # First, determine required counts
        # If dept_id is 'all', sum requirement across all departments, otherwise get selected department requirement
        if dept_id == "all":
            required_daily = sum(d["required_employees_per_day"] for d in departments_list)
        else:
            selected_dept = next((d for d in departments_list if str(d["department_id"]) == dept_id), None)
            required_daily = selected_dept["required_employees_per_day"] if selected_dept else 0.0

        required_hourly = required_daily / 24.0

        for d_str in dates_to_calculate:
            coverage_data[d_str] = []
            curr_date_dt = datetime.strptime(d_str, "%Y-%m-%d")
            prev_date_str = (curr_date_dt - timedelta(days=1)).strftime("%Y-%m-%d")

            for h in range(24):
                active_shifts = []
                for s in raw_shifts:
                    # Filter by department if applicable
                    if dept_id != "all":
                        if str(s["department_id"]) != dept_id:
                            continue

                    # Parse start/end times
                    start_val = parse_time_to_float(s["start_time"])
                    end_val = parse_time_to_float(s["end_time"])

                    is_active = False
                    # Case 1: Shift date is exactly the day we are checking
                    if s["shift_date"] == d_str:
                        if start_val <= end_val:
                            # Standard same-day shift (e.g. 09:00 to 17:00)
                            if start_val < h + 1 and end_val > h:
                                is_active = True
                        else:
                            # Overnight shift starting on d_str (e.g. 22:00 to 06:00 next day)
                            if start_val < h + 1:
                                is_active = True
                    # Case 2: Shift date was the day before d_str (overnight spillover)
                    elif s["shift_date"] == prev_date_str:
                        if start_val > end_val:
                            # Overnight shift that covers the morning of d_str
                            if end_val > h:
                                is_active = True

                    if is_active:
                        active_shifts.append(s)

                scheduled_count = len(active_shifts)

                # Determine status color-code category
                if required_hourly == 0:
                    status = "inactive" if scheduled_count == 0 else "overstaffed"
                else:
                    if scheduled_count == 0:
                        status = "unattended"
                    elif scheduled_count < required_hourly:
                        status = "understaffed"
                    elif scheduled_count > required_hourly:
                        status = "overstaffed"
                    else:
                        status = "optimal"

                coverage_data[d_str].append({
                    "hour": h,
                    "hour_label": f"{h:02d}:00",
                    "scheduled_count": scheduled_count,
                    "required_count": round(required_hourly, 2),
                    "status": status,
                    "employees": [f"{s['first_name']} {s['last_name']}" for s in active_shifts]
                })

    # Prepare Month View calendar data structure if view is month
    month_calendar = []
    month_label = ""
    if view == "month":
        month_label = current_dt.strftime("%B %Y")
        year = current_dt.year
        month = current_dt.month
        cal = calendar.Calendar(firstweekday=6) # Starts Sunday
        month_weeks_days = cal.monthdayscalendar(year, month)

        for week in month_weeks_days:
            week_days_data = []
            for day in week:
                if day == 0:
                    week_days_data.append({"day": 0, "date_str": "", "stats": None})
                else:
                    day_str = f"{year}-{month:02d}-{day:02d}"
                    day_hours = coverage_data.get(day_str, [])

                    unattended_hrs = sum(1 for h in day_hours if h["status"] == "unattended")
                    understaffed_hrs = sum(1 for h in day_hours if h["status"] == "understaffed")
                    optimal_hrs = sum(1 for h in day_hours if h["status"] == "optimal")
                    overstaffed_hrs = sum(1 for h in day_hours if h["status"] == "overstaffed")
                    inactive_hrs = sum(1 for h in day_hours if h["status"] == "inactive")

                    week_days_data.append({
                        "day": day,
                        "date_str": day_str,
                        "stats": {
                            "unattended": unattended_hrs,
                            "understaffed": understaffed_hrs,
                            "optimal": optimal_hrs,
                            "overstaffed": overstaffed_hrs,
                            "inactive": inactive_hrs
                        }
                    })
            month_calendar.append(week_days_data)

    # Week view days formatting
    week_days = []
    if view == "week":
        for d_str in dates_to_calculate:
            d_dt = datetime.strptime(d_str, "%Y-%m-%d")
            week_days.append({
                "date_str": d_str,
                "label": d_dt.strftime("%a %m/%d"),
                "day_name": d_dt.strftime("%A")
            })

    return render_template(
        "index.html",
        employee_count=employee_count,
        shift_count=shift_count,
        departments=departments_list,
        selected_dept_id=dept_id,
        selected_view=view,
        selected_date=date_str,
        prev_day=prev_day,
        next_day=next_day,
        prev_week=prev_week,
        next_week=next_week,
        prev_month=prev_month,
        next_month=next_month,
        coverage_data=coverage_data,
        month_calendar=month_calendar,
        month_label=month_label,
        week_days=week_days
    )



# -------------------------
# EMPLOYEE READ
# -------------------------

@app.route("/employees")
def employees():
    conn = db()
    data = conn.execute("""
        SELECT employees.*, departments.name as department_name
        FROM employees
        LEFT JOIN departments ON employees.department_id = departments.department_id
    """).fetchall()
    return render_template("employees.html", employees=data)


# -------------------------
# EMPLOYEE CREATE
# -------------------------

@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    conn = db()
    if request.method == "POST":
        dept_id = request.form.get("department_id")
        dept_id = int(dept_id) if dept_id else None
        conn.execute(
            """
            INSERT INTO employees
            (first_name, last_name, phone, email, position, department_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.form["first_name"],
                request.form["last_name"],
                request.form["phone"],
                request.form["email"],
                request.form["position"],
                dept_id
            )
        )
        conn.commit()
        return redirect("/employees")

    depts = conn.execute("SELECT * FROM departments").fetchall()
    return render_template("add_employee.html", departments=depts)


# -------------------------
# EMPLOYEE UPDATE
# -------------------------

@app.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    conn = db()
    if request.method == "POST":
        dept_id = request.form.get("department_id")
        dept_id = int(dept_id) if dept_id else None
        conn.execute(
            """
            UPDATE employees
            SET first_name=?, last_name=?, phone=?, email=?, position=?, department_id=?
            WHERE employee_id=?
            """,
            (
                request.form["first_name"],
                request.form["last_name"],
                request.form["phone"],
                request.form["email"],
                request.form["position"],
                dept_id,
                id
            )
        )
        conn.commit()
        return redirect("/employees")

    employee = conn.execute("SELECT * FROM employees WHERE employee_id=?", (id,)).fetchone()
    depts = conn.execute("SELECT * FROM departments").fetchall()
    return render_template("edit_employee.html", employee=employee, departments=depts)


# -------------------------
# EMPLOYEE DELETE
# -------------------------

@app.route("/delete_employee/<int:id>")
def delete_employee(id):
    conn = db()
    conn.execute("DELETE FROM employees WHERE employee_id=?", (id,))
    conn.commit()
    return redirect("/employees")


# -------------------------
# DEPARTMENT CRUD
# -------------------------

@app.route("/departments")
def departments():
    conn = db()
    data = conn.execute("SELECT * FROM departments").fetchall()
    return render_template("departments.html", departments=data)


@app.route("/add_department", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        conn = db()
        try:
            conn.execute(
                "INSERT INTO departments (name, description, required_employees_per_day) VALUES (?, ?, ?)",
                (
                    request.form["name"],
                    request.form["description"],
                    float(request.form["required_employees_per_day"])
                )
            )
            conn.commit()
            return redirect("/departments")
        except sqlite3.IntegrityError:
            return render_template("add_department.html", error="Department name already exists.")
    return render_template("add_department.html")


@app.route("/edit_department/<int:id>", methods=["GET", "POST"])
def edit_department(id):
    conn = db()
    if request.method == "POST":
        try:
            conn.execute(
                "UPDATE departments SET name=?, description=?, required_employees_per_day=? WHERE department_id=?",
                (
                    request.form["name"],
                    request.form["description"],
                    float(request.form["required_employees_per_day"]),
                    id
                )
            )
            conn.commit()
            return redirect("/departments")
        except sqlite3.IntegrityError:
            dept = conn.execute("SELECT * FROM departments WHERE department_id=?", (id,)).fetchone()
            return render_template("edit_department.html", department=dept, error="Department name already exists.")
    
    dept = conn.execute("SELECT * FROM departments WHERE department_id=?", (id,)).fetchone()
    return render_template("edit_department.html", department=dept)


@app.route("/delete_department/<int:id>")
def delete_department(id):
    conn = db()
    conn.execute("UPDATE employees SET department_id = NULL WHERE department_id = ?", (id,))
    conn.execute("DELETE FROM departments WHERE department_id = ?", (id,))
    conn.commit()
    return redirect("/departments")





# -------------------------
# SHIFT READ
# -------------------------


@app.route("/shifts")

def shifts():


    conn=db()


    data=conn.execute(

    """

    SELECT shifts.*, employees.first_name

    FROM shifts

    LEFT JOIN employees

    ON shifts.employee_id=employees.employee_id

    """

    ).fetchall()



    return render_template(

        "shifts.html",

        shifts=data

    )





# -------------------------
# SHIFT CREATE
# -------------------------


@app.route("/add_shift",
methods=["GET","POST"])

def add_shift():


    conn=db()


    if request.method=="POST":


        conn.execute(

        """

        INSERT INTO shifts

        (
        employee_id,
        shift_date,
        day_of_week,
        start_time,
        end_time,
        position_required
        )

        VALUES(?,?,?,?,?,?)

        """,

        (

        request.form["employee_id"],

        request.form["shift_date"],

        request.form["day"],

        request.form["start"],

        request.form["end"],

        request.form["position"]

        ))


        conn.commit()


        return redirect("/shifts")



    employees=conn.execute(

    "SELECT * FROM employees"

    ).fetchall()



    return render_template(

        "add_shift.html",

        employees=employees

    )





# -------------------------
# SHIFT UPDATE
# -------------------------


@app.route("/edit_shift/<int:id>",
methods=["GET","POST"])

def edit_shift(id):


    conn=db()



    if request.method=="POST":


        conn.execute(

        """

        UPDATE shifts

        SET employee_id=?,

        shift_date=?,

        day_of_week=?,

        start_time=?,

        end_time=?,

        position_required=?

        WHERE shift_id=?

        """,

        (

        request.form["employee_id"],

        request.form["shift_date"],

        request.form["day"],

        request.form["start"],

        request.form["end"],

        request.form["position"],

        id

        ))



        conn.commit()


        return redirect("/shifts")



    shift=conn.execute(

    "SELECT * FROM shifts WHERE shift_id=?",

    (id,)

    ).fetchone()



    employees=conn.execute(

    "SELECT * FROM employees"

    ).fetchall()



    return render_template(

        "edit_shift.html",

        shift=shift,

        employees=employees

    )





# -------------------------
# SHIFT DELETE
# -------------------------


@app.route("/delete_shift/<int:id>")

def delete_shift(id):


    conn=db()


    conn.execute(

    "DELETE FROM shifts WHERE shift_id=?",

    (id,)

    )


    conn.commit()


    return redirect("/shifts")




if __name__=="__main__":

    app.run(debug=True, port=5001)