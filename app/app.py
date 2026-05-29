from flask import Flask, request, render_template
import mysql.connector
app = Flask(__name__)

USER = 'cs461ehr'
HOST = 'localhost'
PW = 'password'

@app.route("/doctor-login",methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        pass
    if request.method == "GET":
        return render_template("login.html",doctor_login=True)

@app.route("/patient-login",methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        pass
    if request.method == "GET":
        return render_template("login.html",doctor_login=False)
