#!python

from flask import Flask, render_template, redirect, jsonify, request, session
import json
import hashlib
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
    print(flower)
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("SELECT * FROM SIGHTINGS WHERE NAME=? ORDER BY SIGHTED DESC LIMIT 10", (flower,))
    ret = c.fetchall()
    conn.close()
    return ret

# Note: Python SQLite3 treats each execute as part of a transaction.  All queries up to the next commit() are part of a single transaction, and can be rolled back using rollback().
def updateFlower(flower, genus, species):
    #print(flower, genus, species)
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("UPDATE FLOWERS SET GENUS=?, SPECIES=? WHERE COMNAME=?", (genus, species, flower))
    ret = c.fetchall()
    conn.commit()
    conn.close()
    return ret

def insertSighting(name, person, loc, sighted):
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("INSERT INTO SIGHTINGS VALUES(?,?,?,?)", (name, person, loc, sighted))
    ret = c.fetchall()
    conn.commit()
    conn.close()
    return ret

def setupDatabase():
    '''
        Setup the log table, triggers, and indices
    '''
    # Copy the database file, and delete any existing database file if it exists
    import os
    import shutil

    if os.path.isfile('flowers.db'):
        os.remove('flowers.db')
    
    shutil.copyfile('database/flowers.db', 'flowers.db')

    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()

    # Create the log table, user table, logging triggers, and indexes
    c.executescript("""CREATE TABLE LOG (EVENT TEXT NOT NULL, TIME datetime default current_timestamp);
                    
                    CREATE TABLE USERS (USER TEXT NOT NULL, HASH TEXT NOT NULL);

                    CREATE TRIGGER INSERT_FLOWERS AFTER INSERT ON FLOWERS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Inserting into FLOWERS values: ' || NEW.GENUS || ', ' || NEW.SPECIES || ', ' || NEW.COMNAME);
                    END;
                    
                    CREATE TRIGGER INSERT_FEATURES AFTER INSERT ON FEATURES
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Inserting into FEATURES values: ' || NEW.LOCATION || ', ' || NEW.CLASS || ', ' || NEW.LATITUDE || ', ' || NEW.LONGITUDE || ', ' || NEW.MAP || ', ' || NEW.ELEV);
                    END;
                    
                    CREATE TRIGGER INSERT_SIGHTINGS AFTER INSERT ON SIGHTINGS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Inserting into SIGHTINGS values: ' || NEW.NAME || ', ' || NEW.PERSON || ', ' || NEW.LOCATION || ', ' || NEW.SIGHTED);
                    END;
                    
                    CREATE TRIGGER UPDATE_FLOWERS AFTER UPDATE ON FLOWERS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Updating FLOWERS values: ' || OLD.GENUS || ', ' || OLD.SPECIES || ', ' || OLD.COMNAME || ' to: ' || NEW.GENUS || ', ' || NEW.SPECIES || ', ' || NEW.COMNAME);
                    END;

                    CREATE TRIGGER UPDATE_FEATURES AFTER UPDATE ON FEATURES
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Updating FEATURES values: ' || OLD.LOCATION || ', ' || OLD.CLASS || ', ' || OLD.LATITUDE || ', ' || OLD.LONGITUDE || ', ' || OLD.MAP || ', ' || OLD.ELEV || ' to: ' || NEW.LOCATION || ', ' || NEW.CLASS || ', ' || NEW.LATITUDE || ', ' || NEW.LONGITUDE || ', ' || NEW.MAP || ', ' || NEW.ELEV);
                    END;

                    CREATE TRIGGER UPDATE_SIGHTINGS AFTER UPDATE ON SIGHTINGS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Updating SIGHTINGS values: ' || OLD.NAME || ', ' || OLD.PERSON || ', ' || OLD.LOCATION || ', ' || OLD.SIGHTED || ' to: ' || NEW.NAME || ', ' || NEW.PERSON || ', ' || NEW.LOCATION || ', ' || NEW.SIGHTED);
                    END;

                    CREATE TRIGGER DELETE_FLOWERS AFTER DELETE ON FLOWERS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Deleting from FLOWERS values: ' || OLD.GENUS || ', ' || OLD.SPECIES || ', ' || OLD.COMNAME);
                    END;
                    
                    CREATE TRIGGER DELETE_FEATURES AFTER DELETE ON FEATURES
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Deleting from FEATURES values: ' || OLD.LOCATION || ', ' || OLD.CLASS || ', ' || OLD.LATITUDE || ', ' || OLD.LONGITUDE || ', ' || OLD.MAP || ', ' || OLD.ELEV);
                    END;
                    
                    CREATE TRIGGER DELETE_SIGHTINGS AFTER DELETE ON SIGHTINGS
                    BEGIN
                        INSERT INTO LOG(EVENT) values('Deleting from SIGHTINGS values: ' || OLD.NAME || ', ' || OLD.PERSON || ', ' || OLD.LOCATION || ', ' || OLD.SIGHTED);
                    END;

                    CREATE INDEX SIGHTINGS_NAME ON SIGHTINGS(NAME);
                    
                    CREATE INDEX SIGHTINGS_PERSON ON SIGHTINGS(PERSON);
                    
                    CREATE INDEX SIGHTINGS_LOCATION ON SIGHTINGS(LOCATION);
    
                    CREATE INDEX SIGHTINGS_SIGHTED ON SIGHTINGS(SIGHTED);
    """)
    conn.commit()
    
    conn.close()
    return

# For the purposes of this assignment, the flowers.db is assumed to be a fresh copy of the flowers database
setupDatabase()
app = Flask(__name__)
app.secret_key = 'plzjustenditall'

@app.route('/log')
def log():
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("SELECT * FROM LOG")
    ret = c.fetchall()
    conn.close()
    return render_template("log.html", content = ret)

@app.route('/')
def index():
    if "loggedin" in session:
        return redirect("/flowers")
    return app.send_static_file('login.html')

@app.route('/register')
def register():
    if "loggedin" in session:
        return redirect("/flowers")
    return app.send_static_file('register.html')


def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

@app.route('/register', methods=['POST'])
def register_new():
    username = request.form['user']
    password = request.form['pass']
    cpassword = request.form['pass-confirm']
    #print(username)
    #print(encrypt_string(password))
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("INSERT INTO USERS VALUES(?,?)", (username, encrypt_string(password)))
    ret = c.fetchall()
    conn.commit()
    conn.close()

    return app.send_static_file('login.html')

@app.route('/', methods=['POST'])
def login():
    '''
        Process login information. Save user in session.
    '''
    username = request.form['user']
    password = request.form['pass']
    conn = sqlite3.connect('flowers.db')
    c = conn.cursor()
    c.execute("SELECT HASH FROM USERS WHERE USER=?", (username,))
    ret = c.fetchall()
    conn.close()
    if len(ret) < 1:
        return app.send_static_file('login.html')

    if ret[0][0] == encrypt_string(password):
        session["loggedin"] = True
        return redirect("/flowers")

    return app.send_static_file('login.html')

@app.route('/logout')
def logout():
    if "loggedin" in session:
        session.pop("loggedin", None)
    return redirect("/")

@app.route('/flowers')
def flowers():
    '''
        Show all flowers and fetch images from google
    '''
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
    hists = zip(imgs, flowers)
     
    return render_template('flowers.html', hists = hists)

@app.route('/flowers', methods=['POST'])
def update():
    print(request.form)
    if "insert-sighting" in request.form:
        person = request.form['person']
        location = request.form['location']
        sighted = request.form['sighted']
        f = request.form['flower-input']
        insertSighting(f, person, location, sighted)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    g = request.form['genus']
    s = request.form['species']
    f = request.form['flower-input']
    updateFlower(f, g, s)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/recent', methods=['POST'])
def recent():
    sightings = queryFlower(request.form['flower'])
    # ignore the name
    sightings = [i[1:] for i in sightings]
    return json.dumps({'success':True, 'sightings':sightings}), 200, {'ContentType':'application/json'} 


app.run(debug=True)
