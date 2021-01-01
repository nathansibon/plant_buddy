import sqlite3 as sql


con = sql.connect('my_plants.db')
cur = con.cursor()
'''con.execute('select count(*) from houseplants where need_water="1" OR water_warning="1"')
con.commit()

'''
k = []
cur.execute('SELECT name, species FROM houseplants WHERE death != 1 and sold != 1 ORDER BY name ASC')
for i in cur.fetchall():
    k.append(i[0] + ' ' + i[1])
print(k)

con.close()

