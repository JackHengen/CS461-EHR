import csv
import random
import re
from dotenv import load_dotenv
import os
from openai import OpenAI

DIRECTORY = "synthea_data"

def map_patients(patient_rows):
    i = 0
    patients = dict()
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

        patients[row["Id"]] = dat

        i+=1
    return patients

def map_docs(doc_rows):
    i = 0
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
    for row in doc_rows:
        dat = {
                "id":i,
                "fname":re.sub(r'\d+$','',row["FIRST"]),
                "lname":re.sub(r'\d+$','',row["LAST"])
        }
        dat["specialty"] = random.choice(specialties)
        docs[row['Id']] = dat
        i+=1
    return docs

# commas
def sqlify_patients(patients):
    s = f'INSERT INTO Patient VALUES\n'
    parts = []
    for p in patients.values():
        parts.append(f"\t({p['id']},'{p['fname'].replace("'","''")}','{p['lname'].replace("'","''")}','{p['sex']}','{p['gender']}','{p['pronouns']}','{p['dob']}')")
    s += ",\n".join(parts)
    s += '\n;'
    return s

# commas
def sqlify_docs(docs):
    s = f'INSERT INTO Doctor VALUES\n'
    parts = []
    for d in docs.values():
        parts.append(f"\t({d['id']},'{d['specialty']}','{d['fname']}','{d['lname']}')")
    s += ",\n".join(parts)
    s += '\n;'
    return s

# commas
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

# commas
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
    with open(f"{DIRECTORY}/medications.csv") as f:
        return list(csv.DictReader(f))
    
def process_medications(med_data):
    load_dotenv()
    medications = {row["CODE"]: row["DESCRIPTION"] for row in med_data}

    med_prompt = """
    I have a list of medications that I need to convert from a single string to a CSV of medication_name, dosage, and description
    Something like:
    Abuse-Deterrent 12 HR  15 MG Extended Release Oral Tablet 
    -> 
    Oxycodone Hydrochloride,   15 MG, Abuse-Deterrent 12 HR Extended Release Oral Tablet

    DO NOT ADD A HEADER LINE
    THE ONLY FORMATTING TO CONSIDER IS TO ONLY HAVE 3 COMMAS PER LINE SEPERATING THE FIELDS, DO NOT USE ANY COMMAS EXCEPT AS SEPERATORS
    DO NOT ADD ANY FORMATTING, BLOCKQUOTES, ANYTHING ELSE

    Please convert for all these rows pasted below:
    """
    for i,med in medications.items():
        med_prompt += f"{i},{med.replace(",",";")}\n"
    
    # print(med_prompt)

    client = OpenAI()
    response = client.responses.create(
        model="gpt-4o-mini",
        input = med_prompt
    )
    
    csv = response.output_text
    medications = []
    i = 0
    for line in csv.split("\n"):
        # print(line)
        try:
            name, dosage, description = line.split(",")
            medications.append({"id":i, "name":name.strip(), "dosage":dosage.strip(), "description":description.strip()})
            i += 1
        except:
            continue

    return medications


# commas
def sqlify_medications(medications):
    s = "INSERT INTO Medication VALUES\n"
    parts = []
    for m in medications:
        parts.append(f"\t({m["id"]},'{m["name"]}','{m["dosage"]}','{m["description"]}')")
    s += ",\n".join(parts)
    s += "\n;"
    return s


if __name__ == "__main__":
    patients, docs = get_patients_and_docs_data()
    patients = map_patients(patients)
    docs = map_docs(docs)
    print('USE CS461_EHR;')
    print(sqlify_patients(patients))
    print(sqlify_docs(docs))
    patient_docs = generate_patient_docs(patients,docs)
    print(sqlify_patient_docs(patient_docs))
    medications = get_medications_data()
    medications = process_medications(medications)
    print(sqlify_medications(medications))
