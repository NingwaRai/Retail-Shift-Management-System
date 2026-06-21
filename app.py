from flask import Flask, render_template, request, redirect
import sqlite3

from database import create_tables


app = Flask(__name__)


create_tables()


def db():

    conn = sqlite3.connect(
        "retail_shift_management.db"
    )

    conn.row_factory = sqlite3.Row

    return conn



@app.route("/")
def home():
    conn = db()
    employee_count = conn.execute("SELECT COUNT(*) as count FROM employees").fetchone()["count"]
    shift_count = conn.execute("SELECT COUNT(*) as count FROM shifts").fetchone()["count"]
    return render_template("index.html", employee_count=employee_count, shift_count=shift_count)



# -------------------------
# EMPLOYEE READ
# -------------------------

@app.route("/employees")

def employees():

    conn=db()

    data=conn.execute(
        "SELECT * FROM employees"
    ).fetchall()

    return render_template(
        "employees.html",
        employees=data
    )



# -------------------------
# EMPLOYEE CREATE
# -------------------------

@app.route("/add_employee",
methods=["GET","POST"])

def add_employee():


    if request.method=="POST":


        conn=db()


        conn.execute(
        """
        INSERT INTO employees
        (first_name,last_name,phone,email,position)

        VALUES(?,?,?,?,?)

        """,
        (

        request.form["first_name"],

        request.form["last_name"],

        request.form["phone"],

        request.form["email"],

        request.form["position"]

        ))


        conn.commit()


        return redirect("/employees")



    return render_template(
        "add_employee.html"
    )




# -------------------------
# EMPLOYEE UPDATE
# -------------------------


@app.route("/edit_employee/<int:id>",
methods=["GET","POST"])

def edit_employee(id):


    conn=db()


    if request.method=="POST":


        conn.execute(

        """
        UPDATE employees

        SET first_name=?,
        last_name=?,
        phone=?,
        email=?,
        position=?

        WHERE employee_id=?

        """,

        (

        request.form["first_name"],

        request.form["last_name"],

        request.form["phone"],

        request.form["email"],

        request.form["position"],

        id

        ))


        conn.commit()


        return redirect("/employees")



    employee=conn.execute(

    "SELECT * FROM employees WHERE employee_id=?",

    (id,)

    ).fetchone()



    return render_template(
        "edit_employee.html",
        employee=employee
    )




# -------------------------
# EMPLOYEE DELETE
# -------------------------


@app.route("/delete_employee/<int:id>")

def delete_employee(id):


    conn=db()


    conn.execute(

    "DELETE FROM employees WHERE employee_id=?",

    (id,)

    )


    conn.commit()


    return redirect("/employees")





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