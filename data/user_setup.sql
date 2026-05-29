USE CS461_EHR;

DROP USER IF EXISTS 'cs461ehr'@'localhost';
CREATE USER 'cs461ehr'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON CS461_EHR.* to 'cs461ehr'@'localhost';
