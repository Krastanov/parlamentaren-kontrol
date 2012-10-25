import psycopg2

# Return unicode instead of 'UTF-8' encoded str
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

db = psycopg2.connect(database="parlamentarenkontrol", user="parlamentarenkontrol")
cur = db.cursor()
subcur = db.cursor()


