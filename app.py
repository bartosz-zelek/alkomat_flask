from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

@app.route('/')
def index():
    list_of_employees = [["1", "23:52 5.11.2023 r.", "Bartosz Żelek", "0.2‰", "Dopuszczony"], ["2", "23:52 5.11.2023 r.", "Żartosz Belek", "2.0‰", "Niedopuszczony"]]
    return render_template('home.html', list_of_employees=list_of_employees)