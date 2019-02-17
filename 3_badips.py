#!/usr/bin/python
# -*- coding: utf-8 -*-

#CREATE DATABASE badips;
#        USE badips;
#
#CREATE TABLE badips (
#        ip CHAR(15) NOT NULL
#        );
#
import sys
reload(sys)
sys.setdefaultencoding('UTF8')

execfile('config.inc.py')


import csv
import MySQLdb as mdb
con = mdb.connect(host=sql['host'], user=sql['user'], passwd=sql['password'], db=sql['db'], charset='utf8');
cursor = con.cursor(mdb.cursors.DictCursor)

import requests
links = ["https://www.badips.com/get/list/ssh/1","https://www.badips.com/get/list/voip/1","https://www.badips.com/get/list/bruteforce/1","http://lists.blocklist.de/lists/all.txt","http://www.voipbl.org/update/"]

sql = []
for link in links:
  r = requests.get(link)

  csv_reader = csv.reader(r.text.splitlines(), delimiter=',')
  for row in csv_reader:
    if row[0] not in sql and row[0][0] != "#":
      sql.append(row[0])


cursor.execute("DELETE FROM `badips`")
con.commit()

print "Inserting into database..."
for i in range(len(sql)):
  cursor.execute("INSERT INTO `badips` SET `ip`='%s'"%(sql[i]))
  if i%500 == 0:
    con.commit()
con.commit()




