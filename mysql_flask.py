# references: 
#   flask quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
#   mysql python documentation: https://dev.mysql.com/doc/connector-python/en/

# first steps:
#   pip install flask
#   pip install mysql-connector-python

from flask import Flask
import mysql.connector

app = Flask(__name__)

USER = 'cs461ehr'
HOST = 'localhost'
PW = 'password'

@app.route("/")
def hello_world():
    html = "<h1>Patients</h1>\n"
    with mysql.connector.connect(user=USER, password=PW, host=HOST,database='CS461_EHR') as cnx:
        with cnx.cursor() as c:
            c.execute("SELECT fname, lname FROM Patient")
            res = c.fetchall()
            for fname, lname in res:
                html += f"<p>{fname} {lname}</p>"
    return html

@app.route("/add-user",methods=["POST"])
def add_user():
    return """
    <html>
        <body>
            <h2>Login Form</h2>
            <form method="POST" action="/submit">
                <input type="text" name="fname" placeholder="First Name">
                <input type="text" name="lname" placeholder="Last Name">
                <input type="text" name="sex" placeholder="Sex">
                <input type="text" name="gender" placeholder="Gender">
                <input type="text" name="pronouns" placeholder="Pronouns">
                <input type="text" name="dob" placeholder="Date Of Birth">
                <button type="submit">Submit</button>
            </form>
        </body>
    </html>
    """

@app.route("/add-user",methods=["POST"])
def add_user():
    fname = request.form["fname"]
    lname = request.form["lname"]
    sex= request.form["sex"]
    gender = request.form["gender"]
    pronouns = request.form["pronouns"]
    dob = request.form["dob"]


    with mysql.connector.connect(user=USER, password=PW, host=HOST,database='CS461_EHR') as cnx:
        with cnx.cursor() as c:
            c.execute("INSERT INTO patient (fname, lname, sex, gender, pronouns, dob) VALUES (%s, %s, %s, %s, %s, %s)", (fname, lname, sex, gender, pronouns, dob))




# How to connect to the database:
# import mysql.connector
# cnx = mysql.connector.connect(user='user', password='pw', host='124.12.123.123',database='medicine')
# 
# How to process results from a query:
# c = cnx.cursor()
# dob = datetime.date(2004,12,0)
# c.execute("SELECT fname, lname, dob FROM users WHERE dob > %s AND fname LIKE %",dob,"J%") # I am Jack Hengen and my birthday is 12-09-2004
# for fname, lname, dob_res in cursor:
#     printf("Found: {fname} {lname} born on {dob_res}")
# 
