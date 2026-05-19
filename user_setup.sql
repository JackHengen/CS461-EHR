USE CS461_EHR;
CREATE USER 'cs461ehr'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON CS461_EHR.* to 'cs461ehr'@'localhost';
