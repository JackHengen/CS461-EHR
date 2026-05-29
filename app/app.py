from flask import Flask, request, render_template, session, redirect
from mysql import connector
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

                c.execute("SELECT pw FROM Doctor WHERE fname = %s AND lname = %s",[fname,lname])
                pw = c.fetchone()
                if not pw:
                    raise NotImplementedError("incorrect user")
                else:
                    pw= pw[0]
                if not bcrypt.checkpw(request.form["password"].encode(),pw.encode()):
                    raise NotImplementedError("incorrect pw")

                session["user_doctor"] = True
                session["fname"] = fname
                session["lname"] = lname

                return redirect("/")

    if request.method == "GET":
        if session.get("fname"):
            return redirect("/")
        return render_template("login.html",doctor_login=True)

@app.route("/patient-login",methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        with connector.connect(user=USER,password=PW, host=HOST, database=DB) as cnx:
            with cnx.cursor() as c:
                fname = request.form["firstname"]
                lname = request.form["lastname"]

                c.execute("SELECT pw FROM Patient WHERE fname = %s AND lname = %s",[fname,lname])
                pw = c.fetchone()
                if not pw:
                    raise NotImplementedError("incorrect user")
                else:
                    pw= pw[0]
                if not bcrypt.checkpw(request.form["password"].encode(),pw.encode()):
                    raise NotImplementedError("incorrect pw")

                session["user_patient"] = True
                session["fname"] = fname
                session["lname"] = lname

                return redirect("/")

    if request.method == "GET":
        if session.get("fname"):
            return redirect("/")
        return render_template("login.html",doctor_login=False)

@app.route("/")
def home():
    doctor_status = session.get("user_doctor",False)
    patient_status = session.get("user_patient",False)
    fname = session.get("fname")
    lname = session.get("lname")
    return render_template("index.html",user_doctor=doctor_status,user_patient=patient_status,fname=fname,lname=lname)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
