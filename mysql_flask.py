# pip install flask
# pip install mysql-connector-python

from flask import Flask
import mysql.connector as connector

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

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
