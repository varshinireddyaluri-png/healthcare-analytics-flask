
import pandas as pd
import config

# Connect to MySQL
mydb = config.connect()

# Read patients
patients = pd.read_sql(
    "SELECT * FROM patients",
    mydb
)

print("PATIENT RECORDS")
print(patients.head())

# Read visits
visits = pd.read_sql(
    "SELECT * FROM visits",
    mydb
)

print("\nVISIT RECORDS")
print(visits.head())

# Read measurements
measurements = pd.read_sql(
    "SELECT * FROM measurements",
    mydb
)

print("\nMEASUREMENT RECORDS")
print(measurements.head())

mydb.close()
