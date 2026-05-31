from flask import Flask, request, render_template, session, redirect, flash
from mysql import connector
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = "my-secret-key" # just to make session work

USER = 'cs461ehr'
HOST = 'localhost'
PW = 'password'
DB = 'CS461_EHR'

@app.route("/doctor-login",methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        with connector.connect(user=USER,password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:
                fname = request.form["firstname"]
                lname = request.form["lastname"]

                try:
                    c.execute("SELECT pw FROM Doctor WHERE fname = %s AND lname = %s",[fname,lname])
                except:
                    flash("Database issue please contact us")
                    return redirect("/doctor-login")
                pw = c.fetchone()
                if not pw:
                    flash("Incorrect user info")
                    return redirect("/doctor-login")
                else:
                    pw= pw[0]
                if not bcrypt.checkpw(request.form["password"].encode(),pw.encode()):
                    flash("Incorrect password")
                    return redirect("/patient-login")

                session["doctor"] = True
                session["fname"] = fname
                session["lname"] = lname

                return redirect("/")

    if request.method == "GET":
        if session.get("fname"):
            return redirect("/")
        return render_template("login.html",doctor=True)

@app.route("/patient-login",methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        with connector.connect(user=USER,password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:
                fname = request.form["firstname"]
                lname = request.form["lastname"]

                try:
                    c.execute("SELECT pw FROM Patient WHERE fname = %s AND lname = %s",[fname,lname])
                except:
                    flash("Database issue please contact us")
                    return redirect("/patient-login")
                pw = c.fetchone()
                if not pw:
                    flash("Incorrect user info")
                    return redirect("/patient-login")
                else:
                    pw= pw[0]
                if not bcrypt.checkpw(request.form["password"].encode(),pw.encode()):
                    flash("Incorrect password")
                    return redirect("/patient-login")

                session["fname"] = fname
                session["lname"] = lname

                return redirect("/")

    if request.method == "GET":
        if session.get("fname"):
            return redirect("/")
        return render_template("login.html",doctor=False)

@app.route("/patient-onboard",methods=["GET", "POST"])
def patient_onboard():
    if request.method == "POST":
        fname = request.form["firstname"]
        lname = request.form["lastname"]
        pw = bcrypt.hashpw(request.form["password"].encode(),bcrypt.gensalt()).decode()
        dob = datetime.strptime(request.form["dateofbirth"], "%Y-%m-%d").date()

        sex = request.form["sex"] if request.form["sex"] != "null" else None
        gender = request.form["gender"] if request.form["gender"] != "null" else None
        if gender == "Other":
            gender = request.form["othergender"]
        pronouns = request.form["pronouns"] if request.form["pronouns"] != "null" else None
        if pronouns == "Other":
            pronouns = request.form["otherpronouns"]

        with connector.connect(user=USER,password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:
                try:
                    c.execute("""INSERT INTO Patient(fname,lname,sex,gender,pronouns,dob,pw)
                                VALUES (%s,%s,%s,%s,%s,%s,%s)""", [fname,lname,sex,gender,pronouns,dob,pw])
                except Exception as e:
                    print(e)
                    flash("Database issue please contact us")
                    return redirect("/patient-onboard")

            cnx.commit()
        flash("Successful account creation")
        return redirect("/patient-login")

    if request.method == "GET": 
        if session.get("fname"):
            return redirect("/")
        return render_template("onboard.html",doctor=False)

@app.route("/")
def home():
    fname = session.get("fname")
    if not fname:
        return redirect("/patient-login")
    lname = session.get("lname")

    doctor = session.get("doctor",False)

    return render_template("index.html",doctor=doctor,fname=fname,lname=lname)

@app.route("/logout")
def logout():
    if session.get("doctor"):
        session.clear()
        return redirect("/doctor-login")
    else:
        session.clear()
        return redirect("/")

@app.route("/appointments-patient")
def appointments_patient():
    fname = session.get("fname")
    lname = session.get("lname")

    if not fname:
        return redirect("/patient-login")

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor(dictionary=True) as c:

            c.execute("""
                SELECT pid FROM Patient
                WHERE fname = %s AND lname = %s
            """, [fname, lname])

            result = c.fetchone()
            if not result:
                flash("Patient not found")
                return redirect("/patient-login")

            pid = result["pid"]

            c.execute("""
                SELECT *
                FROM Appointment
                WHERE pid = %s
            """, [pid])

            appointments = c.fetchall()


    return render_template("appointments-patient.html", appointments=appointments)

@app.route("/create-appointment", methods=["GET", "POST"])
def create_appointment():

    if request.method == "POST":
        fname = session.get("fname")
        lname = session.get("lname")

        appointment_time = datetime.strptime(
            request.form["appointment_date"],
            "%Y-%m-%dT%H:%M"
        )

        reason = request.form["reason"]

        with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:

                c.execute("""
                    SELECT pid FROM Patient
                    WHERE fname = %s AND lname = %s
                """, [fname, lname])

                result = c.fetchone()
                if not result:
                    flash("Patient not found")
                    return redirect("/patient-login")

                pid = result[0]

                c.execute("""
                    SELECT did
                    FROM PatientDoctor
                    WHERE pid = %s
                """, [pid])

                doctor = c.fetchone()
                if not doctor:
                    did = 1
                else:
                    did = doctor[0]

                c.execute("""
                    SELECT 1 FROM Appointment
                    WHERE pid = %s AND appointment_time = %s
                """, [pid, appointment_time])

                if c.fetchone():
                    flash("You already have an appointment at this time.")
                    return redirect("/appointments-patient")

                c.execute("""
                    SELECT 1 FROM Appointment
                    WHERE did = %s AND appointment_time = %s
                """, [did, appointment_time])

                if c.fetchone():
                    flash("Doctor is not available at this time.")
                    return redirect("/appointments-patient")

                c.execute("""
                    INSERT INTO Appointment(pid, did, appointment_time, reason)
                    VALUES (%s, %s, %s, %s)
                """, [pid, did, appointment_time, reason])

            cnx.commit()

        flash("Appointment scheduled successfully")
        return redirect("/appointments-patient")

    if not session.get("fname"):
        return redirect("/patient-login")

    return render_template("create-appointment.html")

@app.route("/delete-appointment", methods=["POST"])
def delete_appointment():
    fname = session.get("fname")
    lname = session.get("lname")

    if not fname:
        return redirect("/patient-login")

    did = request.form["did"]
    appointment_time = request.form["appointment_time"]

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor(dictionary=True) as c:

            c.execute("""
                SELECT pid
                FROM Patient
                WHERE fname = %s AND lname = %s
            """, [fname, lname])

            patient = c.fetchone()

            if not patient:
                flash("Patient not found")
                return redirect("/patient-login")

            pid = patient["pid"]

            c.execute("""
                DELETE FROM Appointment
                WHERE pid = %s
                  AND did = %s
                  AND appointment_time = %s
            """, [pid, did, appointment_time])

            cnx.commit()

    flash("Appointment deleted.")
    return redirect("/appointments-patient")