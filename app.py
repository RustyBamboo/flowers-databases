#!python

from flask import Flask, render_template
from google_images_download import google_images_download
from io import StringIO


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
