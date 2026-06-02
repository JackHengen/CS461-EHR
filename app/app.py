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

def login(doctor:bool):
    if request.method == "POST":
        with connector.connect(user=USER,password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:
                fname = request.form["firstname"]
                lname = request.form["lastname"]

                if doctor:
                    r = "/doctor-login"
                else:
                    r = "/patient-login"

                try:
                    if doctor:
                            c.execute("SELECT pw FROM Doctor WHERE fname = %s AND lname = %s",[fname,lname])
                    else:
                        c.execute("SELECT pw FROM Patient WHERE fname = %s AND lname = %s",[fname,lname])
                except:
                    flash("Database issue please contact us")
                    return redirect(r)

                pw = c.fetchone()
                if not pw:
                    flash("Incorrect user info")
                    return redirect(r)
                else:
                    pw= pw[0]
                if not bcrypt.checkpw(request.form["password"].encode(),pw.encode()):
                    flash("Incorrect password")
                    return redirect(r)

                if doctor:
                    session["doctor"] = True
                session["fname"] = fname
                session["lname"] = lname

                return redirect("/")
    else:
        if request.method == "GET":
            if session.get("fname"):
                return redirect("/")
            return render_template("login.html",doctor=doctor)


@app.route("/doctor-login",methods=["GET", "POST"])
def doctor_login():
    return login(True)

@app.route("/patient-login",methods=["GET", "POST"])
def patient_login():
    return login(False)

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

@app.route("/create-appointment", methods=["GET", "POST"])
def create_appointment():
    is_doctor = session.get("doctor", False)

    if not session.get("fname"):
        return redirect("/doctor-login" if is_doctor else "/patient-login")

    if request.method == "POST":
        fname = session.get("fname")
        lname = session.get("lname")

        try:
            appointment_time = datetime.strptime(
                request.form["appointment_date"],
                "%Y-%m-%dT%H:%M"
            )
        except Exception as e:
            print(e)
            flash("Please input required fields")
            return redirect("/create-appointment")

        reason = request.form["reason"]

        with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:

                if is_doctor:
                    c.execute("SELECT did FROM Doctor WHERE fname = %s AND lname = %s", [fname, lname])
                    result = c.fetchone()
                    if not result:
                        flash("Doctor not found")
                        return redirect("/doctor-login")
                    did = result[0]
                    pid = request.form["pid"]

                    c.execute("SELECT 1 FROM Appointment WHERE did = %s AND appointment_time = %s", [did, appointment_time])
                    if c.fetchone():
                        flash("You already have an appointment at this time.")
                        return redirect("/create-appointment")

                    c.execute("SELECT 1 FROM Appointment WHERE pid = %s AND appointment_time = %s", [pid, appointment_time])
                    if c.fetchone():
                        flash("Patient is not available at this time.")
                        return redirect("/create-appointment")

                else:
                    c.execute("SELECT pid FROM Patient WHERE fname = %s AND lname = %s", [fname, lname])
                    result = c.fetchone()
                    if not result:
                        flash("Patient not found")
                        return redirect("/patient-login")
                    pid = result[0]

                    c.execute("SELECT did FROM PatientDoctor WHERE pid = %s", [pid])
                    doctor = c.fetchone()
                    did = doctor[0] if doctor else 1

                    c.execute("SELECT 1 FROM Appointment WHERE pid = %s AND appointment_time = %s", [pid, appointment_time])
                    if c.fetchone():
                        flash("You already have an appointment at this time.")
                        return redirect("/create-appointment")

                    c.execute("SELECT 1 FROM Appointment WHERE did = %s AND appointment_time = %s", [did, appointment_time])
                    if c.fetchone():
                        flash("Doctor is not available at this time.")
                        return redirect("/create-appointment")

                try:
                    c.execute("""
                        INSERT INTO Appointment(pid, did, appointment_time, reason)
                        VALUES (%s, %s, %s, %s)
                    """, [pid, did, appointment_time, reason])
                except Exception as e:
                    print(e)
                    flash("Please input required fields")
                    return redirect("/create-appointment")

            cnx.commit()

        flash("Appointment scheduled successfully")
        return redirect("/appointments")

    return render_template("create-appointment.html", doctor=is_doctor)

@app.route("/file-prescriptions",methods=["GET","POST"])
def file_prescriptions():
    fname = session.get("fname")
    lname = session.get("lname")
    doctor = session.get("doctor", False)

    if not fname or not lname or not doctor:
        return redirect("/")

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor(dictionary=True) as c:
            if request.method == "POST":
                pid = request.form["pid"]
                mid = request.form["mid"]

                try:
                    c.execute("""
                        INSERT INTO PatientMedication(pid, mid)
                        VALUES (%s, %s)
                    """, [pid, mid])

                    cnx.commit()
                    flash("Prescription filed successfully")
                except Exception as e:
                    print(e)
                    flash("Database issue please contact us")

                return redirect("/prescriptions")

            else:
                c.execute("""
                    SELECT pid, fname, lname
                    FROM Patient
                    ORDER BY lname, fname
                """)
                patients = c.fetchall()

                c.execute("""
                    SELECT mid, name, dosage, description
                    FROM Medication
                    ORDER BY name
                """)
                medications = c.fetchall()

                return render_template(
                    "file-prescriptions.html",
                    patients=patients,
                    medications=medications,
                    doctor=doctor
                )


@app.route("/prescriptions", methods=["GET", "POST"])
def prescriptions():
    fname = session.get("fname")
    lname = session.get("lname")
    doctor = session.get("doctor", False)

    if not fname or not fname or doctor:
        return redirect("/")


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

            c.execute("""
                SELECT m.mid, m.name, m.dosage, m.description
                FROM Medication m
                JOIN PatientMedication pm ON m.mid = pm.mid
                WHERE pm.pid = %s
            """, [patient["pid"]])

            prescriptions = c.fetchall()

    return render_template("prescriptions.html", doctor=doctor, prescriptions=prescriptions)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    fname = session.get("fname")
    lname = session.get("lname")

    if not fname:
        return redirect("/patient-login")

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor(dictionary=True) as c:

            c.execute("""
                SELECT pid, fname, lname
                FROM Patient
                WHERE fname = %s AND lname = %s
            """, [fname, lname])

            patient = c.fetchone()

            if not patient:
                flash("Patient not found")
                return redirect("/patient-login")

            pid = patient["pid"]

            if request.method == "POST":

                action = request.form.get("action")

                try:
                    if action == "add_email":
                        email = request.form["email_addr"]

                        c.execute("""
                            INSERT INTO PatientEmail(pid, email_addr)
                            VALUES (%s, %s)
                        """, [pid, email])

                    elif action == "delete_email":
                        email = request.form["email_addr"]

                        c.execute("""
                            DELETE FROM PatientEmail
                            WHERE pid = %s
                              AND email_addr = %s
                        """, [pid, email])

                    elif action == "add_phone":
                        phone = request.form["phone_num"]

                        c.execute("""
                            INSERT INTO PatientPhone(pid, phone_num)
                            VALUES (%s, %s)
                        """, [pid, phone])

                    elif action == "delete_phone":
                        phone = request.form["phone_num"]

                        c.execute("""
                            DELETE FROM PatientPhone
                            WHERE pid = %s
                              AND phone_num = %s
                        """, [pid, phone])

                    cnx.commit()
                    flash("Profile updated successfully")

                except Exception as e:
                    print(e)
                    flash("Database issue please contact us")

                return redirect("/profile")

            c.execute("""
                SELECT email_addr
                FROM PatientEmail
                WHERE pid = %s
                ORDER BY email_addr
            """, [pid])

            emails = c.fetchall()

            c.execute("""
                SELECT phone_num
                FROM PatientPhone
                WHERE pid = %s
                ORDER BY phone_num
            """, [pid])

            phones = c.fetchall()

    return render_template(
        "profile.html",
        doctor=False,
        patient=patient,
        emails=emails,
        phones=phones
    )

@app.route("/appointments")
def appointments_doctor():
    fname = session.get("fname")
    lname = session.get("lname")

    doctor = session.get("doctor",False)

    if not fname:
        return redirect("/")

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor(dictionary=True) as c:
            if doctor:
                c.execute("""
                    SELECT did as uid FROM Doctor
                    WHERE fname = %s AND lname = %s
                """, [fname, lname])
            else:
                c.execute("""
                    SELECT pid as uid FROM Patient
                    WHERE fname = %s AND lname = %s
                """, [fname, lname])

            result = c.fetchone()

            if not result:
                flash("Your account could not be found in the system")
                return redirect("/")

            uid = result["uid"]

            field = "did" if doctor else "pid"
            c.execute(f"""
                SELECT *
                FROM Appointment
                WHERE {field} = %s
            """, [uid])

            appointments = c.fetchall()

    return render_template("appointments.html", doctor=doctor, appointments=appointments)

@app.route("/delete-appointment", methods=["POST"])
def delete_appointment():
    fname = session.get("fname")
    lname = session.get("lname")
    is_doctor = session.get("doctor", False)

    if not fname:
        return redirect("/doctor-login" if is_doctor else "/patient-login")

    pid = request.form.get("pid")
    did = request.form.get("did")
    appointment_time = request.form.get("appointment_time")

    if not pid or not did or not appointment_time:
        flash("Missing appointment data")
        return redirect("/appointments")

    with connector.connect(user=USER, password=PW, host=HOST, database=DB) as cnx:
        with cnx.cursor() as c:
            c.execute("""
                DELETE FROM Appointment
                WHERE pid = %s AND did = %s AND appointment_time = %s
            """, [pid, did, appointment_time])
            cnx.commit()

    flash("Appointment deleted.")
    return redirect("/appointments")
