DROP DATABASE IF EXISTS CS461_EHR;
CREATE DATABASE CS461_EHR;

USE CS461_EHR;

CREATE TABLE Patient(
    pid INT AUTO_INCREMENT,
    fname VARCHAR(255) NOT NULL,
    lname VARCHAR(255) NOT NULL,
    sex ENUM('M','F'),
    gender VARCHAR(255),
    pronouns VARCHAR(10),
    dob DATE NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    pw VARCHAR(255) NOT NULL,
    PRIMARY KEY (pid)
);

CREATE TABLE PatientMeasurement(
    pid INT,
    date_of_measurement DATE NOT NULL,
    height_in FLOAT,
    weight_lb FLOAT,
    bp_sys FLOAT,
    bp_dia FLOAT,
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE PatientEmail(
    pid INT,
    email_addr VARCHAR(255) NOT NULL,
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE PatientPhone(
    pid INT,
    phone_num VARCHAR(50) NOT NULL,
    FOREIGN KEY (pid) REFERENCES Patient(pid)
);

CREATE TABLE Doctor(
    did INT AUTO_INCREMENT,
    specialty VARCHAR(255),
    fname VARCHAR(255) NOT NULL,
    lname VARCHAR(255) NOT NULL,
    pw VARCHAR(255) NOT NULL,
    PRIMARY KEY (did)
);

CREATE TABLE Appointment(
    pid INT,
    did INT,
    appointment_time DATETIME NOT NULL,
    reason VARCHAR(255),
    PRIMARY KEY (pid, did, appointment_time),
    FOREIGN KEY (pid) REFERENCES Patient(pid),
    FOREIGN KEY (did) REFERENCES Doctor(did)
);


CREATE TABLE Medication(
    mid INT AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    dosage VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    PRIMARY KEY (mid)
);

CREATE TABLE PatientDoctor(
    pid INT,
    did INT,
    PRIMARY KEY (pid, did),
    FOREIGN KEY (pid) REFERENCES Patient(pid),
    FOREIGN KEY (did) REFERENCES Doctor(did)
);

CREATE TABLE PatientMedication(
    pid INT,
    mid INT,
    PRIMARY KEY (pid, mid),
    FOREIGN KEY (pid) REFERENCES Patient(pid),
    FOREIGN KEY (mid) REFERENCES Medication(mid)
);
