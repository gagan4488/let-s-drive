import base64
import pandas as pd
import pyodbc
import matplotlib
from matplotlib import pyplot as plt
from io import BytesIO

plotdata = pd.DataFrame(
    {"pies": [10, 10, 42, 17, 37]},
    index=["Dad", "Mam", "Bro", "Sis", "Me"])
# Plot a bar chart
plotdata.plot(kind="bar")
print("done")
conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server=DESKTOP-4SBKB3C\SQLEXPRESS;"
                      "Database=mydb;"
                      "Trusted_Connection=yes;")

cursor = conn.cursor()

sql1 = "SELECT C.Car_Type, count(R.User_userName) as Total_Users from Reservation as R, Car as C " \
       "where R.Car_VIN= C.VIN " \
       "group by C.Car_Type Order By  count(R.User_userName) DESC;"
df = pd.read_sql(sql1, conn)

plot1 = df.plot().get_figure()
img = BytesIO()
plot1.savefig(img, format='png')
img.seek(0)
buffer = b''.join(img)
b2 = base64.b64encode(buffer)
