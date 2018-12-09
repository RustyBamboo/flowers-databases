#!python

from flask import Flask, render_template
from google_images_download import google_images_download
from io import StringIO
import sqlite3

def queryFlowerList(c):
    c.execute("SELECT COMNAME FROM FLOWERS")
    return c.fetchall()

def queryFlower(c, flower):
    c.execute("SELECT * FROM SIGHTINGS WHERE NAME=? ORDER BY SIGHTED DESC LIMIT 10", flower)
    return c.fetchall()

# Note: Python SQLite3 treats each execute as part of a transaction.  All queries up to the next commit() are part of a single transaction, and can be rolled back using rollback().
def updateFlower(c, loc, clas, lat, lng, mp, elev):
    c.execute("UPDATE FEATURES SET CLASS=?, LATITUDE=?, LONGITUDE=?, MAP=?, ELEV=?, WHERE LOCATION=?", clas, lat, lng, mp, elev, loc)
    ret = c.fetchall()
    c.commit()
    return ret

def insertSighting(c, name, person, loc, sighted):
    c.execute("INSERT INTO SIGHTINGS VALUES(?,?,?,?)", name, person, loc, sighted)
    ret = c.fetchall()
    c.commit()
    return ret

def setupDatabase(c):
    '''
        Setup the log table, triggers, and indices
    '''
    c.execute("CREATE TABLE LOG (EVENT TEXT NOT NULL, TIME datetime default current_timestamp)")
    # INSERT INTO LOG(EVENT) values('test') query for logging trigger
    c.commit()
    return

# For the purposes of this assignment, the flowers.db is assumed to be a fresh copy of the flowers database
conn = sqlite3.connect('flowers.db')
c = conn.cursor()
setupDatabase(c)
app = Flask(__name__)

@app.route('/flowers')
def flowers():
    '''
        Show all flowers and fetch images from google
    '''

    import os
   
    flower_name = 'flower'
    output_directory = 'static/flower_imgs'
    if flower_name not in os.listdir(output_directory):
        arguments = {"keywords":flower_name,"output_directory": output_directory, "no_directory": True, "limit":1,"print_urls":True} 
        response = google_images_download.googleimagesdownload()
        path = response.download(arguments)
        print(path[flower_name])
        os.rename(path[flower_name][0], output_directory + '/' + flower_name)

    imgs = os.listdir(output_directory)
    imgs = ['flower_imgs/' + file for file in imgs]
     
    return render_template('flowers.html', hists = imgs)

app.run(debug=True)
