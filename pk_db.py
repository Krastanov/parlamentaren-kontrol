import psycopg2

db = psycopg2.connect(database="parlamentarenkontrol", user="parlamentarenkontrol")
cur = db.cursor()
