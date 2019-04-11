from datetime import datetime

f = open("count.txt", 'w')
f.write(str(datetime(year=2019, month=4, day=8, hour=9)))
f.close()