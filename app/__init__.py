import os
from flask import Flask, render_template, send_from_directory
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', title="MLH Fellow", url=os.getenv("URL"))

@app.route('/portfolio')
def portfolio(): 
    return render_template('portfolio.html', title="Portfolio", url=os.getenv("URL"))

@app.route('/resume')
def resume(): 
    return render_template('resume.html', title="Resume", url=os.getenv("URL"))

@app.route('/contact')
def contact(): 
    return render_template('contact.html', title="Contact", url=os.getenv("URL"))
