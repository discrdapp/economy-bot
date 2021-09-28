import sqlite3

import config

def fetchOne(sql):
	conn = sqlite3.connect(config.db)

	cursor = conn.execute(sql) 
	data = cursor.fetchone()
	conn.close()

	return data