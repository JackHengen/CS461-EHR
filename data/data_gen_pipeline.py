import csv
import random
import re
from dotenv import load_dotenv
import os
from openai import OpenAI
import datetime as dt
import bcrypt

DIRECTORY = "synthea_data"

def generate_password():
    pw = ""
    for i in range(random.randrange(8,16)):
        if random.random() > .5:
            pw += chr(random.randint(65,90))
        else:
            pw += chr(random.randint(97,122))
    return pw


def map_patients(patient_rows):
    i = 1
    patients = dict()
    with open("patients.txt", 'w') as f:
        for row in patient_rows:
            dat = {
                "id":i,
                "dob":row['BIRTHDATE'],
                'fname':re.sub(r'\d+$','',row['FIRST']),
                'lname':re.sub(r'\d+$','',row["LAST"]),
                'sex':row["GENDER"]
            }

            gend_ran = random.random()
            if gend_ran < .01:
                if dat['sex'] == 'F':
                    dat['gender'] = 'M'
                else:
                    dat['gender'] = 'F'
            elif gend_ran < .05:
                dat['gender'] = 'N'
            else:
                dat['gender'] = dat['sex']

            if dat['gender'] == 'N':
                dat['pronouns'] = 'they/them'
            elif dat['gender'] == 'F':
                dat['pronouns'] = 'she/her'
            elif dat['gender'] == 'M':
                dat['pronouns'] = 'he/him'

            pw = generate_password()
            f.write(f"fname:{dat['fname']},lname:{dat['lname']},pw:{pw}\n")
            dat['pw'] = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode().replace("'","''")

            patients[row["Id"]] = dat

            i+=1


    return patients

def map_docs(doc_rows):
    i = 1
    docs = dict()
    specialties = [
            'Cardiology',
            'Dermatology',
            'Neurology',
            'Orthopedics',
            'Pediatrics',
            'Psychiatry',
            'Oncology',
            'Gastroenterology',
            'Endocrinology',
            'Pulmonology',
            'Nephrology',
            'Rheumatology',
            'Ophthalmology',
            'Urology',
            'Obstetrics & Gynecology',
            'Emergency Medicine',
            'Radiology',
            'Anesthesiology',
            'Infectious Disease',
            'General Surgery'
    ]
    with open("docs.txt",'w') as f:
        for row in doc_rows:
            dat = {
                    "id":i,
                    "fname":re.sub(r'\d+$','',row["FIRST"]),
                    "lname":re.sub(r'\d+$','',row["LAST"])
            }

            dat["specialty"] = random.choice(specialties)

            pw = generate_password()
            f.write(f"fname:{dat['fname']},lname:{dat['lname']},pw:{pw}\n")
            dat['pw'] = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode().replace("'","''")

            docs[row['Id']] = dat

            i+=1

    return docs

def sqlify_patients(patients):
    s = 'INSERT INTO Patient VALUES\n'
    parts = []
    for p in patients.values():
        parts.append(f"\t({p['id']},'{p['fname'].replace("'","''")}','{p['lname'].replace("'","''")}','{p['sex']}','{p['gender']}','{p['pronouns']}','{p['dob']}','{p['pw']}')")
    s += ",\n".join(parts)
    s += '\n;'
    return s

def sqlify_docs(docs):
    s = 'INSERT INTO Doctor VALUES\n'
    parts = []
    for d in docs.values():
        parts.append(f"\t({d['id']},'{d['specialty']}','{d['fname']}','{d['lname']}','{d['pw']}')")
    s += ",\n".join(parts)
    s += '\n;'
    return s

def generate_patient_docs(patients,docs):
    mappings = []
    docs = list(docs.values())
    for patient in patients.values():
        num_docs = round(random.gauss(1,.5))
        if num_docs < 1:
            num_docs = 1
        patient_docs = set()
        pid = patient["id"]
        for _ in range(num_docs):
            while (did := random.choice(docs)["id"]) in patient_docs:
                continue
            patient_docs.add(did)
            mappings.append((pid,did))
    return mappings

def sqlify_patient_docs(patient_docs):
    s = "INSERT INTO PatientDoctor VALUES\n"
    parts = []
    for p,d in patient_docs:
        parts.append(f"\t({p},{d})")
    s += ",\n".join(parts)
    s += '\n;'
    return s

def get_patients_and_docs_data():
    with open(f"{DIRECTORY}/patients.csv") as f:
        data = list(csv.DictReader(f))
        keep_docs = round(.1 * len(data))
        patient_rows, doc_rows = data[:-keep_docs], data[-keep_docs:]
    return patient_rows, doc_rows

def get_medications_data():
    medications = {}
    med_patient_mapping = []
    with open(f"{DIRECTORY}/medications.csv") as f:
        for row in csv.DictReader(f):
            medications[row["CODE"]] = row["DESCRIPTION"]
            med_patient_mapping.append((row["PATIENT"],row["CODE"]))

    return medications, med_patient_mapping



def process_medications(med_data):
    load_dotenv()

    med_prompt = """
    I have a list of medications in the format code,string that I need to convert to a CSV of code, medication_name,
    dosage, and description by converting the string into the medication_name, dosage, and description
    Something like:
    12345, Abuse-Deterrent 12 HR  15 MG Extended Release Oral Tablet
    ->
    12345, Oxycodone Hydrochloride,   15 MG, Abuse-Deterrent 12 HR Extended Release Oral Tablet

    DO NOT ADD A HEADER LINE
    THE ONLY FORMATTING TO CONSIDER IS TO ONLY HAVE 3 COMMAS PER LINE SEPERATING THE FIELDS, DO NOT USE ANY COMMAS EXCEPT AS SEPERATORS
    DO NOT ADD ANY FORMATTING, BLOCKQUOTES, ANYTHING ELSE

    Please convert for all these rows pasted below:
    """
    for code,med in med_data.items():
        med_prompt += f"{code},{med.replace(",",";")}\n"

    # print(med_prompt)

    client = OpenAI()
    response = client.responses.create(
        model="gpt-4o-mini",
        input=med_prompt
    )

    csv = response.output_text
    medications = dict()
    i = 1
    for line in csv.split("\n"):
        # print(line)
        try:
            code, name, dosage, description = line.split(",")
            if code not in med_data:
                # hallucinated random medication code
                continue
            medications[code.strip()]= {"id":i, "name":name.strip(), "dosage":dosage.strip(), "description":description.strip()}
            i += 1
        except:
            continue

    return medications

def generate_patient_emails(patients):
    patient_emails = []

    for patient in patients.values():
        i = patient["id"]
        fname, lname = patient["fname"].replace("'","''"), patient["lname"].replace("'","''")

        chop_front = random.random()
        join_with_symbol = random.random()
        chop_back = random.random()
        numbers_in_back = random.random()
        domain = random.random()

        email = ""
        if chop_front < .15:
            chars = random.randint(1,3)
            email += fname[:chars]
        else:
            email += fname

        if join_with_symbol <.2:
            email += random.choice(['.','_','-'])

        if chop_back < .15:
            chars = random.randint(1,3)
            email += lname[:chars]
        else:
            email += lname

        if numbers_in_back < .2:
            num_of_nums = random.randint(1,5)
            for num in range(num_of_nums):
                email += str(random.randint(1,9))

        email += "@"
        if domain < .45:
            email += "gmail"
        elif domain < .70:
            email += "outlook"
        elif domain < .75:
            email += "hotmail"
        elif domain < .8:
            email += "live"
        elif domain < .85:
            email += "yahoo"
        else:
            email += "icloud"

        email += ".com"

        patient_emails.append((i,email))

    return patient_emails




def generate_patient_phones(patients):
    common_area_codes = [
        "215",
        "267",
        "445",
        "610",
        "484",
        "835",
        "856",
        "302",
        "609",
        "717",
        "223",
    ]

    uncommon_area_codes = [
        "570",
        "272",
        "410",
        "443",
        "667",
        "301",
        "240",
        "202",
        "703",
        "571",
        "973",
        "201",
        "551",
        "732",
        "848",
        "917",
        "718",
        "347",
        "929",
        "646",
    ]

    rare_area_codes = [
        "305",
        "786",
        "404",
        "470",
        "312",
        "773",
        "213",
        "310",
        "424",
        "206",
        "425",
        "617",
        "857",
        "214",
        "469",
        "512",
        "602",
        "702",
        "808",
        "907",
    ]

    phones = []

    for patient in patients.values():
        counts = [0, 1, 2, 3]
        weights = [0.05, 0.7, 0.2, 0.05]

        num_of_phones = random.choices(counts, weights=weights, k=1)[0]
        for i in range(num_of_phones):
            area_rand = random.random()
            if area_rand < .75:
                area_code = random.choice(common_area_codes)
            elif area_rand <.95:
                area_code = random.choice(uncommon_area_codes)
            else:
                area_code = random.choice(rare_area_codes)

            num = area_code + "-"

            for i in range(3):
                num += str(random.randrange(0,10))

            num += "-"

            for i in range(4):
                num += str(random.randrange(0,10))

            phones.append((patient["id"],num))

    return phones

def sqlify_patient_emails(patient_emails):
    s = "INSERT INTO PatientEmail VALUES\n"
    parts = []
    for pid,email in patient_emails:
        parts.append(f"\t({pid},'{email}')")
    s += ",\n".join(parts)
    s += "\n;"
    return s

def sqlify_patient_phones(patient_phones):
    s = "INSERT INTO PatientPhone VALUES\n"
    parts = []
    for pid,phone in patient_phones:
        parts.append(f"\t({pid},'{phone}')")
    s += ",\n".join(parts)
    s += "\n;"
    return s


def sqlify_medications(medications):
    s = "INSERT INTO Medication VALUES\n"
    parts = []
    for m in medications.values():
        parts.append(f"\t({m["id"]},'{m["name"]}','{m["dosage"]}','{m["description"]}')")
    s += ",\n".join(parts)
    s += "\n;"
    return s

def generate_appointments(patient_docs):
    appointment_reasons = [
        "Annual physical",
        "Follow-up visit",
        "Medication refill",
        "Blood pressure check",
        "Diabetes follow-up",
        "Routine checkup",
        "Cold symptoms",
        "Flu symptoms",
        "Cough",
        "Fever",
        "Headache",
        "Migraine",
        "Back pain",
        "Neck pain",
        "Joint pain",
        "Knee pain",
        "Shoulder pain",
        "Chest discomfort",
        "Shortness of breath",
        "Abdominal pain",
        "Nausea",
        "Vomiting",
        "Diarrhea",
        "Constipation",
        "Skin rash",
        "Allergy symptoms",
        "Ear pain",
        "Sore throat",
        "Sinus congestion",
        "Urinary symptoms",
        "Sleep problems",
        "Fatigue",
        "Dizziness",
        "Weight management",
        "Nutrition counseling",
        "Lab review",
        "Vaccination",
        "TB test",
        "Pre-employment physical",
        "Sports physical",
        "School physical",
        "Mental health consultation",
        "Anxiety follow-up",
        "Depression follow-up",
        "Stress management",
        "Smoking cessation",
        "Referral consultation",
        "Post-hospital follow-up",
        "Wound check",
        "General consultation"
    ]

    appointments = []
    for p,d in patient_docs:
        if random.random() > .6:
            # no appointments with doc scheduled
            continue
        start = dt.datetime(2026,6,12)
        end = dt.datetime(2027,1,1)
        delta = end - start

        secs = random.randint(0,int(delta.total_seconds()))
        date = start + dt.timedelta(seconds=secs)

        reason = random.choice(appointment_reasons)
        appointments.append({"pid":p,"did":d,"appointment_time":date,"reason":reason})

    return appointments


def sqlify_appointments(appointments):
    s = "INSERT INTO Appointment VALUES\n"
    parts = []
    for a in appointments:
        parts.append(f"\t({a["pid"]},{a["did"]},'{a["appointment_time"].strftime("%Y-%m-%d %H:%M:%S")}','{a["reason"]}')")
    s += ",\n".join(parts)
    s += "\n;"
    return s

def map_patient_medications(patients,medications,mapping):
    # print(medications)
    new_map = []

    for puid, mcode in mapping:
        if mcode not in medications:
            # hallucination when generating data
            continue
        if puid not in patients:
            # chose the patient as a doctor
            continue
        to_add = (patients[puid]["id"],medications[mcode]["id"])
        if to_add not in new_map:
            # this is because we are mapping prescriptions filled at diff dates (can be duplicate) to our
            # medications field which is meant to be any medications currently b eing taken
            new_map.append(to_add)

    return new_map

def sqlify_patient_medications(patient_medications):
    s = "INSERT INTO PatientMedication VALUES\n"
    parts = []
    for pid,mid in patient_medications:
        parts.append(f"\t({pid},{mid})")
    s += ",\n".join(parts)
    s += "\n;"
    return s

def map_patient_measurements(patients):
    observations = {}
    with open(f"{DIRECTORY}/observations.csv") as f:
        for obs in csv.DictReader(f):
            if obs["DESCRIPTION"] in ["Body Weight","Body Height","Diastolic Blood Pressure","Systolic Blood Pressure"]:
                if obs["PATIENT"] not in patients:
                    # doctors are removed from patients so some of these ids are taken as our doctors
                    continue
                enc = observations.setdefault(obs["ENCOUNTER"],{"pid":patients[obs["PATIENT"]]["id"],"date":dt.datetime.fromisoformat(obs["DATE"])})
                enc[obs["DESCRIPTION"]] = float(obs["VALUE"])

    observations = [obs for obs in observations.values() if "Body Weight" in obs and "Body Height" in obs and "Diastolic Blood Pressure" in obs and "Systolic Blood Pressure" in obs]

    return observations


def sqlify_patient_measurements(patient_measurements):
    s = "INSERT INTO PatientMeasurement VALUES\n"
    parts = []
    for o in patient_measurements:
        parts.append(f"({o["pid"]},'{o["date"].strftime("%Y-%m-%d %H:%M:%S")}',{o["Body Height"]},{o["Body Weight"]},{o["Systolic Blood Pressure"]},{o["Diastolic Blood Pressure"]})")
    s += ",\n".join(parts)
    s += "\n;"
    return s

if __name__ == "__main__":
    print('USE CS461_EHR;')

    patients, docs = get_patients_and_docs_data()
    patients = map_patients(patients)

    print(sqlify_patients(patients))

    patient_emails = generate_patient_emails(patients)
    print(sqlify_patient_emails(patient_emails))

    patient_phones = generate_patient_phones(patients)
    print(sqlify_patient_phones(patient_phones))

    docs = map_docs(docs)
    print(sqlify_docs(docs))

    patient_docs = generate_patient_docs(patients,docs)
    print(sqlify_patient_docs(patient_docs))

    appointments = generate_appointments(patient_docs)
    print(sqlify_appointments(appointments))

    medications, med_patient_map = get_medications_data()
    medications = process_medications(medications)
    print(sqlify_medications(medications))

    patient_medications = map_patient_medications(patients,medications,med_patient_map)
    print(sqlify_patient_medications(patient_medications))

    patient_measurements = map_patient_measurements(patients)
    print(sqlify_patient_measurements(patient_measurements))
