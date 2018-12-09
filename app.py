#!python

from flask import Flask, render_template, redirect, jsonify
from google_images_download import google_images_download
import sqlite3

def queryFlowerList():
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("SELECT COMNAME FROM FLOWERS")
    ret = c.fetchall()
    conn.close()
    return ret

def queryFlower(flower):
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("SELECT * FROM SIGHTINGS WHERE NAME=? ORDER BY SIGHTED DESC LIMIT 10", flower)
    ret = c.fetchall()
    conn.close()
    return ret

# Note: Python SQLite3 treats each execute as part of a transaction.  All queries up to the next commit() are part of a single transaction, and can be rolled back using rollback().
def updateFlower(loc, clas, lat, lng, mp, elev):
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("UPDATE FEATURES SET CLASS=?, LATITUDE=?, LONGITUDE=?, MAP=?, ELEV=?, WHERE LOCATION=?", clas, lat, lng, mp, elev, loc)
    ret = c.fetchall()
    conn.commit()
    conn.close()
    return ret

def insertSighting(name, person, loc, sighted):
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("INSERT INTO SIGHTINGS VALUES(?,?,?,?)", name, person, loc, sighted)
    ret = c.fetchall()
    conn.commit()
    conn.close()
    return ret

def setupDatabase():
    '''
        Setup the log table, triggers, and indices
    '''
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("CREATE TABLE LOG (EVENT TEXT NOT NULL, TIME datetime default current_timestamp)")
    # INSERT INTO LOG(EVENT) values('test') query for logging trigger
    conn.commit()
    conn.close()
    return

# For the purposes of this assignment, the flowers.db is assumed to be a fresh copy of the flowers database
setupDatabase(c)
app = Flask(__name__)

@app.route('/')
def index():
    return redirect('/flowers')

@app.route('/flowers')
def flowers():
    '''
        Show all flowers and fetch images from google
    '''
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()

    import os
    flowers = queryFlowerList()
    flowers = [i[0] for i in flowers]
    # Make sure there are images
    for flower in flowers:
        flower_name = flower + ' flower'
        output_directory = 'static/flower_imgs'
        if flower_name not in os.listdir(output_directory):
            arguments = {"keywords":flower_name,"output_directory": output_directory, "no_directory": True, "limit":1,"print_urls":True} 
            response = google_images_download.googleimagesdownload()
            path = response.download(arguments)
            print(path[flower_name])
            os.rename(path[flower_name][0], output_directory + '/' + flower_name)

    
    imgs = ['flower_imgs/' + f + ' flower' for f in flowers]
    print(imgs)
    hists = zip(imgs, flowers)
     
    return render_template('flowers.html', hists = hists)

app.run(debug=True)
