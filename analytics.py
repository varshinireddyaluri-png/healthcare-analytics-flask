
import matplotlib.pyplot as plt
import pandas as pd
import config

mydb = config.connect()

query = """
SELECT d.department_name,
       COUNT(v.visit_id) AS total_visits
FROM departments d
LEFT JOIN visits v
ON d.department_id = v.department_id
GROUP BY d.department_id, d.department_name
ORDER BY d.department_id
"""

df = pd.read_sql(query, mydb)

mydb.close()

print(df)

plt.figure(figsize=(9, 5))
plt.bar(df["department_name"], df["total_visits"])

plt.title("Synthetic Healthcare Department Visits")
plt.xlabel("Department")
plt.ylabel("Number of Visits")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig("department_visits.png")
plt.show()
