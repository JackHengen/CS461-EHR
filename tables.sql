DROP DATABASE IF EXISTS CS461_EHR;
CREATE DATABASE CS461_EHR;

USE CS461_EHR;

CREATE TABLE Patient(
    pid INT,
    fname VARCHAR(100) NOT NULL,
    lname VARCHAR(100) NOT NULL,
    sex ENUM('MALE','FEMALE'),
    gender VARCHAR(25),
    pronouns VARCHAR(10),
    dob DATE,
    did INT,
    PRIMARY KEY (pid)
    FOREIGN KEY (did) REFERENCES Doctor(did)
);

CREATE TABLE PatientMeasurement(
    pid INT,
    date_of_measurement DATE,
    height_in INT,
    weight_lb INT,
    bp_sys INT,
    bp_dia INT,
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE PatientEmail(
    pid INT,
    email_addr VARCHAR(255),
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE PatientPhone(
    pid INT,
    phone_num VARCHAR(50),
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE Doctor(
    did INT,
    specialty VARCHAR(255),
    fname VARCHAR(255),
    lname VARCHAR(255)
)

CREATE TABLE Medication(
    mid INT,
    name VARCHAR(255),
    dosage INT,
    description VARCHAR(255)
    pid INT,
    FOREIGN KEY (pid) REFERENCES Patient(pid)
)