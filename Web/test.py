import pyodbc

conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server=DESKTOP-4SBKB3C\SQLEXPRESS;"
                      "Database=mydb;"
                      "Trusted_Connection=yes;")

cursor = conn.cursor()
print("done")