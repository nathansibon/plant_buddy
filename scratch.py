import sqlite3 as sql


con = sql.connect('my_plants.db')
cur = con.cursor()
'''con.execute('select count(*) from houseplants where need_water="1" OR water_warning="1"')
con.commit()

'''
cur.execute('SELECT * FROM houseplants WHERE death != 1 and sold != 1 ORDER BY need_water ASC, water_warning ASC')
for i in cur.fetchall():
    print(i)

con.close()

