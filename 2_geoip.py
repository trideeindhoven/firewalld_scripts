#!/usr/bin/python
# -*- coding: utf-8 -*-

#CREATE TABLE IF NOT EXISTS `GeoLite2-Country-Locations-en` (
#  `geoname_id` int(11) NOT NULL,
#  `locale_code` varchar(5) DEFAULT NULL,
#  `continent_code` varchar(5) DEFAULT NULL,
#  `country_iso_code` varchar(5) DEFAULT NULL,
#  `continent_name` varchar(64) DEFAULT NULL,
#  `country_name` varchar(64) DEFAULT NULL,
#  `is_in_european_union` tinyint(4) DEFAULT NULL
#) ENGINE=InnoDB DEFAULT CHARSET=latin1;
#
#CREATE TABLE IF NOT EXISTS `GeoLite2-Country-Blocks-IPv4` (
#  `geoname_id` int(11) NOT NULL,
#  `network` varchar(20) DEFAULT NULL,
#  `registered_country_geoname_id` int(11) DEFAULT NULL,
#  `represented_country_geoname_id` int(11) DEFAULT NULL,
#  `is_anonymous_proxy` tinyint(4) DEFAULT NULL,
#  `is_satellite_provider` tinyint(4) DEFAULT NULL
#) ENGINE=InnoDB DEFAULT CHARSET=latin1;

import sys
reload(sys)
sys.setdefaultencoding('UTF8')

execfile('config.inc.py')

import urllib
urllib.urlretrieve ("https://geolite.maxmind.com/download/geoip/database/GeoLite2-Country-CSV.zip", "/tmp/geoip.zip")

import zipfile
import os
import shutil

with zipfile.ZipFile('/tmp/geoip.zip') as zip_file:
  for member in zip_file.namelist():
    filename = os.path.basename(member)
    # skip directories
    if filename == 'GeoLite2-Country-Blocks-IPv4.csv' or filename == 'GeoLite2-Country-Locations-en.csv':
      source = zip_file.open(member)
      target = file(os.path.join('/tmp', filename), "wb")
      with source, target:
        shutil.copyfileobj(source, target)

os.remove("/tmp/geoip.zip")

import csv
import MySQLdb as mdb
con = mdb.connect(host=sql['host'], user=sql['user'], passwd=sql['password'], db=sql['db'], charset='utf8');
cursor = con.cursor(mdb.cursors.DictCursor)

sql = ["DELETE FROM `GeoLite2-Country-Locations-en`", "DELETE FROM `GeoLite2-Country-Blocks-IPv4`"]

print "Getting: /tmp/GeoLite2-Country-Locations-en.csv"
with open('/tmp/GeoLite2-Country-Locations-en.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
    if line_count == 0:
      #print(f'Column names are {", ".join(row)}')
      line_count += 1
    else:
      sql.append("INSERT INTO `GeoLite2-Country-Locations-en` SET `geoname_id`='%s',`locale_code`='%s',`continent_code`='%s',`country_iso_code`='%s', `continent_name`='%s',`country_name`='%s',`is_in_european_union`='%s'"%(row[0], row[1], row[2], row[4], row[3], row[5], row[6]) )
      line_count += 1

print "Getting: /tmp/GeoLite2-Country-Blocks-IPv4.csv"
with open('/tmp/GeoLite2-Country-Blocks-IPv4.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
    if line_count == 0:
      #print(f'Column names are {", ".join(row)}')
      line_count += 1
    else:
      sql.append("INSERT INTO `GeoLite2-Country-Blocks-IPv4` SET `network`='%s', `geoname_id`='%s', `registered_country_geoname_id`='%s', `represented_country_geoname_id`='%s', `is_anonymous_proxy`='%s', `is_satellite_provider`='%s'"%(row[0], row[1], row[2], row[3], row[4], row[5]) )
      line_count += 1

print "Inserting into database..."
for i in range(len(sql)):
  cursor.execute(sql[i])
  if i%500 == 0:
    con.commit()
con.commit()

