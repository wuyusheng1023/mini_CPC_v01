import mysql.connector

mydb = mysql.connector.connect(
  host="52.47.100.208",
  user="foo",
  passwd="13269358090"
)

print(mydb)

mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

for x in mycursor:
  print(x)


mydb = mysql.connector.connect(
  host="ec2-52-47-100-208.eu-west-3.compute.amazonaws.com",
  user="foo",
  passwd="13269358090"
)

