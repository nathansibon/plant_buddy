import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

con = sql.connect('my_plants.db')

p = pd.read_sql_query('select * from houseplants', con)

print(p.columns)

p['count'] = 1
p['cum'] = p.sort_values('purchase_date')['count'].cumsum()
sub = p[['purchase_date', 'cum', 'name']].sort_values('purchase_date')
print(sub)

# thanks to https://matplotlib.org/3.2.1/gallery/lines_bars_and_markers/timeline.html
# Choose some nice levels
levels = np.tile([-5, 5, -3, 3, -1, 1],
                 int(np.ceil(len(sub['purchase_date'])/6)))[:len(sub['purchase_date'])]

# Create figure and plot a stem plot with the date
fig, ax = plt.subplots(constrained_layout=True, figsize=(10, 5))
ax.set(title='Plant Family Timeline')

markerline, stemline, baseline = ax.stem(sub['purchase_date'], levels,
                                         linefmt="blue", basefmt="k-",
                                         use_line_collection=True)

plt.setp(markerline, mec="k", mfc="w", zorder=3)

# Shift the markers to the baseline by replacing the y-data by zeros.
markerline.set_ydata(np.zeros(len(sub['purchase_date'])))

# annotate lines
vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
for d, l, r, va in zip(sub['purchase_date'], levels, sub['name'], vert):
    ax.annotate(r, xy=(d, l), xytext=(-3, np.sign(l)*3),
                textcoords="offset points", va=va, ha="right")

# remove y axis and spines
ax.get_yaxis().set_visible(False)
for spine in ["left", "top", "right"]:
    ax.spines[spine].set_visible(False)

ax.margins(y=0.1)
plt.savefig('static/my_plants_timeline.png', format='png', dpi=200)
#plt.show()

'''
con = sql.connect('plant_requirements.db')
cur = con.cursor()

o = 'select distinct botanical_name, common_name, light_category, light_tolerance, temp_category, temp_tolerance, rh_category, rh_tolerance, water_category water_tolerance, soil_category from requirements'
old = cur.execute(o)

con.execute('DELETE FROM requirements;')
con.commit()

for i in old:
    print(i)
    q = 'insert into requirements (' \
        'botanical_name, ' \
        'common_name, ' \
        'light_category, ' \
        'light_tolerance, ' \
        'temp_category, ' \
        'temp_tolerance, ' \
        'rh_category, ' \
        'rh_tolerance, ' \
        'water_category, ' \
        'water_tolerance, ' \
        'soil_category) VALUES (?,?,?,?,?,?,?,?,?,?)'
    con.execute(q, i)
    con.commit()

con.close()
'''

