import base64
import os
import random

#import cv2
import datetime

import numpy as np
import pandas as pd
from multiprocessing import shared_memory
from flask import Flask, render_template, url_for, redirect, jsonify, Response, abort, session, request, send_file, flash
from werkzeug.utils import secure_filename
import sqlite3
import shutil
import time
import timetable_generator_module
import qrcode
import pickle
from sendmail import send_mail

#import systemcheck

conn = sqlite3.connect('data.db')
print ("Opened database successfully")


conn.execute('''CREATE TABLE IF NOT EXISTS USERS
         (   USERNAME TEXT PRIMARY KEY,
             PASSWORD           TEXT,
             TYPE               TEXT,
             MAILID             TEXT
                 );''')

conn.execute('''CREATE TABLE IF NOT EXISTS STUDENTS
         (   USERNAME TEXT PRIMARY KEY,
             PASSWORD           TEXT,
             NAME               TEXT,
             MAILID             TEXT,
             HIGHSCHOOL         TEXT,
             HIGHSCHOOL_SCORE   TEXT,
             INTERMIDIATE_SCHOOL    TEXT,       
             INTERMIDIATE_SCORE TEXT,
             BRANCH             TEXT,
             GUARDIAN_NAME      TEXT,
             GUARDIAN_MAIL      TEXT,
             TYPE               TEXT
            
                 );''')



conn.execute('''CREATE TABLE IF NOT EXISTS EXIT_REQUESTS
         (   TIMESTAMP TEXT PRIMARY KEY,
             USERNAME          TEXT,
             REASON          TEXT,
             STATUS             TEXT,
             FACULTY_NAME       TEXT,
             SECURITY_NAME      TEXT,
             EXIT_TIME          TEXT
                 );''')



conn.close()

shape = (480, 640, 3)
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Photos/')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'audioData/')
CAPTURE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'captured_picture/')

user_details = []
last_verify_qr = time.time()

try:
    with open("./static/timetable_list.pkl", "rb") as fp:
        timetable_list = pickle.load(fp)
    with open("./static/other_details_list.pkl", "rb") as fp:
        other_details_list = pickle.load(fp)
    with open("./static/incharge_list.pkl", "rb") as fp:
        incharge_list = pickle.load(fp)
    with open("./static/class_details.pkl", "rb") as fp:
        class_details = pickle.load(fp)
except:
    print("Old Time Table Data not found. Kindly Generate")
    timetable_list, other_details_list, incharge_list, class_details, SUBJECT_COUNT, INCHARGE_COUNT, CLASS_COUNT = [],[],[], ["CSE", "301"], 0, 0, 1
    timetable_list = [
                [ "NO DATA",]*10,
                [ "NO DATA",]*10,
                [ "NO DATA",]*10,
                [ "NO DATA",]*10,
                [ "NO DATA",]*10,
                [ "NO DATA",]*10,
            ]
    other_details_list =[
        ["NO DATA", "NO DATA", "NO DATA"],

    ]
    incharge_list = [
                ["NO DATA", "NO DATA"],
                ["NO DATA", "NO DATA"],
                ["NO DATA", "NO DATA"],
                ["Class Incharge", "NO DATA"],
            ]
    class_details = ["NO DATA", "KINDLY GENERATE"]

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
outputFrame = None
number = random.randint(1000000, 9999999)




def html_return(msg, redirect_to = "/", delay = 5, bgcolor="white"):
    return f"""
                <html>    
                    <head>      
                        <title>Student Desk</title>      
                        <meta http-equiv="refresh" content="{delay};URL='{redirect_to}'" />    
                    </head>    
                    <body style="background-color:{bgcolor}"> 
                        <h2> {msg}</h2>
                        <p>This page will refresh automatically.</p> 
                    </body>  
                </html>   
                
                """

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['get', 'post'])
def home_page():
    return render_template('homepage.html')
   

@app.route('/login/<login_type>', methods=['get', 'post'])
def login_page(login_type):
    global user_details
    print("Login Type:", login_type)
    if request.method == 'POST':
        username, password, account_type = request.form['username'], request.form['password'], request.form['account_type']
        print("Account Type:", account_type)
        if username == "admin" and "admin" in password.lower():
            session['user'] = username
            session['account_type'] = account_type
            session['login_type'] = login_type

            user_details = (session['user'], session['account_type'], session['login_type'])
            print("Render 0")
            return render_template('index.html', user=user_details)
        else:
            try:
                conn = sqlite3.connect('data.db')
                print ("Opened database successfully 1")
                if account_type == "Student":
                    cursor = conn.execute(f"SELECT PASSWORD, USERNAME, TYPE from STUDENTS")
                else:
                    print("Non Student Login")
                    cursor = conn.execute(f"SELECT PASSWORD, USERNAME, TYPE from USERS")
                for row in cursor:
                    print(row[0] , password , row[1] , username , row[2] , account_type)
                    if row[0] == password and row[1] == username and row[2] == account_type:

                        conn.close()

                        session['user'] = username
                        session['account_type'] = account_type
                        session['login_type'] = login_type

                        user_details = (session['user'], session['account_type'], session['login_type'])
                        print("Render 1")
                        return render_template('index.html', user=user_details)
                if "1" in login_type:
                    login_options = ['admin', 'security']
                else:
                    login_options = []
                return render_template('login-page.html', login_options = login_options)
            
            except Exception as e:
                print("DB Error 1: ", e)
    elif 'user' in session.keys():
        print("Render 2")
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('index.html', user=user_details)
    else:
        if "1" in login_type:
            login_options = ['admin', 'security']
        else:
            login_options = []

        return render_template('login-page.html', login_options = login_options)


@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('home_page'))


@app.route('/add_exit_request/', methods=['get', 'post'])
def add_exit_requests():
    print("Add Exit Request Called")
    if 'user' in session.keys():
        if request.method == 'POST':

            conn = sqlite3.connect('data.db')

            username = session['user']
            reason = request.form['reason'].replace('"','').replace("'","")
            account_type = session['account_type']
            timestamp = str(datetime.datetime.now()).replace(" ", "-").replace(":", "-").replace(".", "-")
            status = "Applied"

            cursor = conn.execute(f"SELECT USERNAME, TIMESTAMP, STATUS, FACULTY_NAME,SECURITY_NAME from EXIT_REQUESTS WHERE USERNAME='{session['user']}'")
            curyear = int(datetime.datetime.now().year)
            curmonth = int(datetime.datetime.now().month)
            curday = int(datetime.datetime.now().day)
            for row in cursor:
                
                applied_date = row[1]
                applied_date = row[1].split("-")
                print("ts", applied_date)
                print(curyear, curmonth, curday)
                if curyear == int(applied_date[0]) and curmonth == int(applied_date[1]) and curday == int(applied_date[2]):
                    print("Already Applied") 
                    conn.close()
                    return html_return(f"You have Already Applied for Exit Request Today. Try Again Tomorrow.", redirect_to = "/add_exit_request", delay = 5, bgcolor="red")


            
            conn.execute(f"INSERT INTO EXIT_REQUESTS ( USERNAME, REASON, TIMESTAMP, STATUS, FACULTY_NAME, SECURITY_NAME, EXIT_TIME) VALUES ('{username}', '{reason}', '{timestamp}', '{status}', ' ', ' ', ' ' )")

            cursor = conn.execute(f"SELECT USERNAME, MAILID from USERS WHERE TYPE='Faculty'")
            faculty_mails = ""
            for row in cursor:
                faculty_mails += row[1]
                faculty_mails += ","
               
            conn.commit()
            conn.close()

            send_mail(faculty_mails, "Exit Request Applied", f"Student with Hall Ticket No. {username} applied for Exit. Application ID:{timestamp}. Reason: {reason}")

            return html_return(f"Student with Hall Ticket No. {username} applied successfully for Exit. Application ID:{timestamp}.", redirect_to = "/add_exit_request", delay = 5)
        
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('add_exit_request.html', user=user_details)
    else:
        return redirect(url_for('home_page'))


@app.route('/verify_QR/', methods=['get', 'post'])
def verify_QR():
    global last_verify_qr
    print("verify QR Called")
    
    if 'user' in session.keys():
        if request.method == 'POST':

            timestamp = request.form['timestamp']
            conn = sqlite3.connect('data.db')

            account_type = session['account_type']
            status = "Exited"
            security_name = session['user']
            exit_time = str(datetime.datetime.now())[:-7]

            conn = sqlite3.connect('data.db')
            cursor = conn.execute(f"SELECT USERNAME, STATUS, FACULTY_NAME,SECURITY_NAME from EXIT_REQUESTS WHERE TIMESTAMP='{timestamp}'")
            qr_details = []
            qr_status = ""
            for row in cursor:
                qr_details.append(row)
                qr_status = row[1]

            print("qr_status", qr_status)
            if ("APPR" in qr_status):
                conn.execute(f"UPDATE EXIT_REQUESTS SET STATUS = '{status}', SECURITY_NAME = '{security_name}', EXIT_TIME = '{exit_time}' WHERE TIMESTAMP='{timestamp}'")
                conn.commit()
                conn.close()

                return html_return(f"Student successfully Exited. Application ID:{timestamp}.", redirect_to = "/verify_QR", delay = 5, bgcolor="lightgreen")
            else:
                return html_return(f"QR Invalid.", redirect_to = "/verify_QR", delay = 5, bgcolor="red")

        
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('verify_QR.html', user=user_details)
    else:
        return redirect(url_for('home_page'))


@app.route('/view_exit_requests/', methods=['get', 'post'])
def view_exit_requests():
    print("view exit request called")
    if 'user' in session.keys():
        conn = sqlite3.connect('data.db')
        cursor = conn.execute(f"SELECT USERNAME, TIMESTAMP, STATUS, FACULTY_NAME,SECURITY_NAME from EXIT_REQUESTS WHERE USERNAME='{session['user']}'")
        users_list = []
        for row in cursor:
            users_list.append(row)
        conn.close()

        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('view_exit_requests.html', user=user_details, users_list=users_list)
    else:
        return redirect(url_for('home_page'))


#For Faculty
@app.route('/exit_requests/', methods=['get', 'post'])
def exit_requests():
    print("Exit Requests Called")
    if 'user' in session.keys():
        conn = sqlite3.connect('data.db')
        cursor = conn.execute("SELECT USERNAME, REASON, TIMESTAMP, STATUS, FACULTY_NAME, SECURITY_NAME, EXIT_TIME from EXIT_REQUESTS ORDER BY TIMESTAMP DESC")
        users_list = []
        for row in cursor:
            users_list.append(row)
        conn.close()
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('exit_requests.html', user=user_details, users_list=users_list)
    else:
        return redirect(url_for('home_page'))


@app.route('/exit_accept/<timestamp>')
def exit_accept(timestamp):
    print("Exit Accept Called")
    if 'user' in session.keys():
        conn = sqlite3.connect('data.db')
        print(session['user'], timestamp)
        conn.execute(f"UPDATE EXIT_REQUESTS SET STATUS = 'APPROVED', FACULTY_NAME='{session['user']}' where TIMESTAMP = '{timestamp}'")
        conn.commit()

        cursor = conn.execute(f"SELECT USERNAME, STATUS from EXIT_REQUESTS WHERE TIMESTAMP = '{timestamp}'")
        student_username = ""
        for row in cursor:
            student_username = row[0]

        cursor = conn.execute(f"SELECT USERNAME, MAILID from STUDENTS WHERE USERNAME = '{student_username}'")
        student_mail = ""
        for row in cursor:
            student_mail = row[1]
        conn.close()

        send_mail(student_mail, "Exit Request Accepted", f"Hi, {student_username}, Your Exit Request with Application ID: {timestamp}is Accepted. You can Proceed to Security Gate for Exit")
        
        return redirect(url_for('exit_requests'))
    else:
        return redirect(url_for('home_page'))


@app.route('/exit_reject/<timestamp>')
def exit_reject(timestamp):
    print("Exit Reject Called")
    if 'user' in session.keys():
        conn = sqlite3.connect('data.db')
        conn.execute(f"UPDATE EXIT_REQUESTS SET STATUS = 'REJECTED', FACULTY_NAME='{session['user']}' where TIMESTAMP = '{timestamp}' ")
        conn.commit()

        cursor = conn.execute(f"SELECT USERNAME, STATUS from EXIT_REQUESTS WHERE TIMESTAMP = '{timestamp}'")
        student_username = ""
        for row in cursor:
            student_username = row[0]

        cursor = conn.execute(f"SELECT USERNAME, MAILID from STUDENTS WHERE USERNAME = '{student_username}'")
        student_mail = ""
        for row in cursor:
            student_mail = row[1]
        conn.close()
        
        send_mail(student_mail, "Exit Request Rejected", f"Hi, {student_username}, Your Exit Request with Application ID: {timestamp}is Rejected by {session['user']}.")

        return redirect(url_for('exit_requests'))
    else:
        return redirect(url_for('home_page'))


@app.route('/timetable_generator_details/', methods=['get', 'post'])
def timetable_generator_details():
    print("TimeTable Generator Details Called")
    global SUBJECT_COUNT, INCHARGE_COUNT, CLASS_COUNT
    if 'user' in session.keys():
        if request.method == 'POST':
            
            SUBJECT_COUNT = int(request.form['suject_count'])
            INCHARGE_COUNT = int(request.form['incharge_count'])
            CLASS_COUNT = int(request.form['class_count'])

            print("Counts:", SUBJECT_COUNT, INCHARGE_COUNT, CLASS_COUNT)

            return redirect(url_for('timetable_generator')) 
        
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('timetable_generator_details.html', user=user_details)
    else:
        return redirect(url_for('home_page'))   


@app.route('/timetable_generator/', methods=['get', 'post'])
def timetable_generator():
    print("Timetable Generator Called")
    global SUBJECT_COUNT, INCHARGE_COUNT, CLASS_COUNT, timetable_list, other_details_list, incharge_list, class_details
    if 'user' in session.keys():
        if request.method == 'POST':
            
            subject_details = []
            other_details_list = []
            class_details = []

            print("Countsb:", SUBJECT_COUNT, INCHARGE_COUNT, CLASS_COUNT)

            for i in range(1,SUBJECT_COUNT+1):
                subject_name = request.form[f's{i}name']
                max_periods = request.form[f's{i}duration']
                faculty_name = request.form[f's{i}faculty']
                subject_code = request.form[f's{i}code']

                temp_list = [subject_name, max_periods, "0"]
                temp_list2 = [subject_code, subject_name, faculty_name]

                subject_details.append(temp_list.copy())
                other_details_list.append(temp_list2.copy())



            for i in range(1,CLASS_COUNT+1):
                class_name = request.form[f'c{i}name']
                class_faculty = request.form[f'c{i}faculty']
                class_room = request.form[f'c{i}room']

                temp_list = [class_name, class_faculty, class_room]

                class_details.append(temp_list.copy())
     
            
            incharge_list = []
            for i in range(1,INCHARGE_COUNT+1):
                
                faculty_name = request.form[f'm{i}faculty']
                mentoring_code = request.form[f'm{i}code']

                temp_list = [mentoring_code, faculty_name]
             
                incharge_list.append(temp_list.copy())
            

            # print(subject_details)

            timetable_generator_module.set_subjects(subject_details)
            timetable_generator_module.set_suitable_timing()
            timetable_list = timetable_generator_module.get_desired_timetable(required_timetables=CLASS_COUNT)
            
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            for timetable in timetable_list:
                for i in range(6):
                    timetable[i].insert(0, days[i])

                for i in range(6):
                    timetable[i].insert(3,"Break")
                
                for i in range(6):
                    timetable[i].insert(6,"Lunch")

            with open("./static/timetable_list.pkl", "wb") as fp:
                pickle.dump(timetable_list, fp)
            with open("./static/other_details_list.pkl", "wb") as fp:
                pickle.dump(other_details_list, fp)
            with open("./static/incharge_list.pkl", "wb") as fp:
                pickle.dump(incharge_list, fp)
            with open("./static/class_details.pkl", "wb") as fp:
                pickle.dump(class_details, fp)


            return redirect(url_for('timetable_output'))
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('timetable_generator.html', user=user_details, SUBJECT_COUNT = SUBJECT_COUNT+1, INCHARGE_COUNT = INCHARGE_COUNT+1, CLASS_COUNT=CLASS_COUNT+1)
    else:
        return redirect(url_for('home_page'))


@app.route('/timetable_output/')
def timetable_output():
    print("TimeTable Output Called")
    global timetable_list, other_details_list, incharge_list,  class_details, CLASS_COUNT

    if 'user' in session.keys():
        
        print("class details:",class_details)
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('timetable_output.html', user=user_details, timetable_list=timetable_list, other_details_list = other_details_list, incharge_list = incharge_list, class_details = class_details)
    else:
        return redirect(url_for('home_page'))


@app.route('/add_student/', methods=['get', 'post'])
def add_student():
    print("Add Student Called")
    if 'user' in session.keys():
        if request.method == 'POST':

            if 'file' not in request.files:
                flash('No file part')
                return html_return(f"Make Sure to Upload Student Image in PNG or JPG Format.", redirect_to = "/add_student", delay = 5)

            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return html_return(f"Student {name} bearing Hall Ticket No. {hallticket} with Password {password} added to Database.", redirect_to = "/add_student", delay = 5)
            
            if file and allowed_file(file.filename):


                name = request.form['name']
                hallticket = request.form['hallticket']
                password = request.form['password']
                if len(password) < 2:
                    password = "Student12345"
                mail_id = request.form['mail_id']
                highschool = request.form['highschool']
                highschool_score = request.form['highschool_score']
                intermidiate_school = request.form['intermidiate_school']
                intermidiate_score = request.form['intermidiate_score']
                branch = request.form['branch']
                guardian_name = request.form['guardian_name']
                guardian_mail = request.form['guardian_mail']

                
                # filename = secure_filename(file.filename)
                
                
                print("Updating Database")
                conn = sqlite3.connect('data.db')
                conn.execute(f"INSERT INTO STUDENTS ( USERNAME, PASSWORD, NAME, MAILID, HIGHSCHOOL, HIGHSCHOOL_SCORE, INTERMIDIATE_SCHOOL, INTERMIDIATE_SCORE, BRANCH, GUARDIAN_NAME, GUARDIAN_MAIL, TYPE) VALUES ('{hallticket}', '{password}','{name}', '{mail_id}', '{highschool}', '{highschool_score}', '{intermidiate_school}', '{intermidiate_score}', '{branch}', '{guardian_name}', '{guardian_mail}', 'Student' )")
                conn.commit()
                conn.close()

                file.save(os.path.join(app.config['UPLOAD_FOLDER'], hallticket+".png"))

                return html_return(f"Student {name} bearing Hall Ticket No. {hallticket} with Password {password} added to Database.", redirect_to = "/add_student", delay = 5)
            
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('add_student.html', user=user_details)
    else:
        return redirect(url_for('home_page'))


@app.route('/add_security/', methods=['get', 'post'])
def add_security():
    print("Add Security Called")
    if 'user' in session.keys():
        if request.method == 'POST':
            print("Got security Enroll details")
            username = request.form['username']
            password = request.form['password']
            mailid = request.form['mailid']

            print("Updating Database", end = " ")
            try:
                conn = sqlite3.connect('data.db')
                conn.execute(f"INSERT INTO USERS (USERNAME, PASSWORD, TYPE, MAILID) VALUES ('{username}', '{password}', 'Security', '{mailid}')")
                conn.commit()
                conn.close()
                print("| Security Added Successfully")
                return html_return("Successfully Added Security User: "+str(username), delay = 3)
            except Exception as e:
                print("Failed. ERROR:", e)
         
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('add_security.html', user=user_details)
    else:
        return redirect(url_for('home_page'))


@app.route('/update_security/' , methods=['GET', 'POST'])
def update_security():
    print("Update Security Called")
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got security Update details")
            userid = request.form['username1']
            print("Got userid")
            password = request.form['password1']
            print("Got userid")
            if password == "DEL":
                if userid == '{userid}':
                    try:
                        conn = sqlite3.connect('data.db')
                        conn.execute(f"DELETE from USERS where USERNAME = '{userid}';")
                        conn.commit()
                        conn.close()    
                        return html_return("Successfully Deleted Security User: "+str(userid), delay = 3)
                    except Exception as e:
                        return html_return("Deletion failed for Security User: "+str(userid)+". Reason: "+str(e))
                else:
                    return html_return("Cannot Delete Master Default Security User: "+str(userid))
            else:
                try:
                    conn = sqlite3.connect('data.db')
                    conn.execute(f"UPDATE USERS set PASSWORD = '{password}' where USERNAME = '{userid}';")
                    conn.commit()
                    conn.close()   
                    return html_return("Password Updated for Security: "+str(userid) +" if exists.")
                except Exception as e:
                        return html_return("Password Update failed for Security User: "+str(userid)+". Reason: "+str(e))
    else:
        return redirect(url_for('home_page'))
    


@app.route('/add_faculty/', methods=['get', 'post'])
def add_faculty():
    print("Add Faculty Called")
    if 'user' in session.keys():
        if request.method == 'POST':
            print("Got faculty Enroll details")
            username = request.form['username']
            password = request.form['password']
            mailid = request.form['mailid']

            print("Updating Database", end = " ")
            try:
                conn = sqlite3.connect('data.db')
                conn.execute(f"INSERT INTO USERS (USERNAME, PASSWORD, TYPE, MAILID) VALUES ('{username}', '{password}', 'Faculty', '{mailid}')")
                conn.commit()
                conn.close()
                print("| Admin Added Successfully")
                return html_return("New Faculty Added Successfully "+str(username))
            except Exception as e:
                print("Failed. ERROR:", e)
                return html_return("New Faculty Addition Failed "+str(username)+". Reason: "+str(e))
            
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('add_faculty.html', user=user_details)
    else:
        return redirect(url_for('login_page'))


@app.route('/update_faculty/' , methods=['GET', 'POST'])
def update_faculty():
    print("Update Faculty Called")
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got faculty Update details")
            userid = request.form['username1']
            print("Got userid")
            password = request.form['password1']
            print("Got userid")
            if password == "DEL":
                if userid != "niltech":
                    try:
                        conn = sqlite3.connect('data.db')
                        conn.execute(f"DELETE from USERS where USERNAME = '{userid}';")
                        conn.commit()
                        conn.close()    
                        return html_return("Successfully Deleted Admin User: "+str(userid), delay = 3)
                    except Exception as e:
                        return html_return("Deletion failed for Admin User: "+str(userid)+". Reason: "+str(e))
                else:
                    return html_return("Cannot Delete Master Default Admin User: "+str(userid))
            else:
            
                try:
                    conn = sqlite3.connect('data.db')
                    conn.execute(f"UPDATE USERS set PASSWORD = '{password}' where USERNAME = '{userid}';")
                    conn.commit()
                    conn.close()   
                    return html_return("Password Updated for Admin: "+str(userid) +" if exists.")
                except Exception as e:
                        return html_return("Password Update failed for Admin User: "+str(userid)+". Reason: "+str(e))
    else:
        return redirect(url_for('home_page'))
    
    

@app.route('/all_students/')
def all_students():
    print("All Students Called")
    if 'user' in session.keys():
        conn = sqlite3.connect('data.db')
        # cursor = conn.execute(f"SELECT USERNAME, PASSWORD, NAME, MAILID, HIGHSCHOOL, HIGHSCHOOL_SCORE, INTERMIDIATE_SCHOOL, INTERMIDIATE_SCORE, BRANCH, GUARDIAN_NAME, GUARDIAN_MAIL from STUDENTS")
        cursor = conn.execute(f"SELECT NAME, USERNAME, MAILID, BRANCH, GUARDIAN_NAME, GUARDIAN_MAIL from STUDENTS")
        users_list = []
        for row in cursor:
            users_list.append(row)
        conn.close()
        
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('all_students.html', user=user_details, users_list=users_list)
    else:
        return redirect(url_for('home_page'))









@app.route('/view_QR/<ID>')
def view_QR(ID):
    print("view QR ID Called")
    if 'user' in session.keys():

        conn = sqlite3.connect('data.db')
    
        cursor = conn.execute(f"SELECT USERNAME, PASSWORD, NAME, MAILID, HIGHSCHOOL, HIGHSCHOOL_SCORE, INTERMIDIATE_SCHOOL, INTERMIDIATE_SCORE, BRANCH, GUARDIAN_NAME, GUARDIAN_MAIL from STUDENTS where USERNAME = '{session['user']}'")

        user_data = []
        for row in cursor:
            user_data = row
        conn.close()

        print(user_data)


        img = qrcode.make(str(ID))
        imgname = "./static/"+str(ID)
        img.save(imgname+".png")


        with open(str(imgname)+".png", "rb") as (image):
            image2 = base64.b64encode(image.read()).decode('utf-8')

        with open(UPLOAD_FOLDER + '/' + session['user'] + '.png', 'rb') as (image):
            image = base64.b64encode(image.read()).decode('utf-8')

        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('view_QR.html', user= user_details, image=image, image2=image2, user_data = user_data, timestamp=ID)
    else:
        return redirect(url_for('home_page'))



@app.route('/profile/<ID>')
def profile(ID):
    print("view Profile ID Called")
    if 'user' in session.keys():

        conn = sqlite3.connect('data.db')
    
        cursor = conn.execute(f"SELECT USERNAME, PASSWORD, NAME, MAILID, HIGHSCHOOL, HIGHSCHOOL_SCORE, INTERMIDIATE_SCHOOL, INTERMIDIATE_SCORE, BRANCH, GUARDIAN_NAME, GUARDIAN_MAIL from STUDENTS where USERNAME = '{ID}'")

        user_data = []
        for row in cursor:
            user_data = row
        conn.close()

        print(user_data)

        with open(UPLOAD_FOLDER + '/' + ID + '.png', 'rb') as (image):
            image = base64.b64encode(image.read()).decode('utf-8')

        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('profile.html', user= user_details, image=image, user_data = user_data)
    else:
        return redirect(url_for('home_page'))





@app.route('/cgpa_calculator/', methods=['get', 'post'])
def cgpa_calculator():
    print("cpga calculator called")
    global SUBJECT_COUNT, INCHARGE_COUNT
    if 'user' in session.keys():
        if request.method == 'POST':
            
            SUBJECT_COUNT = int(request.form['suject_count'])
            INCHARGE_COUNT = int(request.form['incharge_count'])

            print("Counts:", SUBJECT_COUNT, INCHARGE_COUNT)

            return redirect(url_for('cgpa_calculator')) 
        
        user_details = (session['user'], session['account_type'], session['login_type'])
        return render_template('cgpa_calculator.html', user=user_details)
    else:
        return redirect(url_for('home_page'))  
    

        
@app.errorhandler(404)
def nice(_):
    return render_template('error_404.html')


# @app.route('/delete_user/<ID>')
# def delete_user(ID):
#     print("delete user ID Called")
#     if 'user' in session.keys():
#         try:
#             conn = sqlite3.connect('data.db')
#             conn.execute(f"DELETE from USER where ID = '{ID}';")
#             conn.commit()
#             conn.close()
#         except Exception as e:
#             print("Unable to delete User from Database. Reason:", e)
#             return jsonify(data=False)
#     else:
#         return redirect(url_for('home_page'))

# @app.route('/download_month/')
# def download_month():
#     if 'user' in session.keys():
#         cur_m = datetime.datetime.now().month
#         cur_y = datetime.datetime.now().year

#         conn = sqlite3.connect('data.db')
#         cursor = conn.execute(f"SELECT NAME, ID, DESIGNATION, DAY, MONTH, YEAR, LOGIN_TIME from ATTENDANCE where MONTH = '{cur_m}' AND YEAR = '{cur_y}'")
#         attendance_list = []
#         for row in cursor:
#             attendance_list.append(row)
#         conn.close()
        
#         name = []
#         rollno = []
#         designation = []
#         date = []
#         login_time = []
        
#         for i in attendance_list:
#             name.append(i[0])
#             rollno.append(i[1])
#             designation.append(i[2])
#             date.append(f"{i[3]}-{i[4]}-{i[5]}")
#             login_time.append(i[6])

#         data = pd.DataFrame({'Name': name, 'ID': rollno, 'Designation': designation, 'Date': date, 'Login_Time': login_time})
#         fname = "Attendance_"+str(cur_m)+"_"+str(cur_y)+'_download.csv'
#         data.to_csv(fname, index=False)
#         return send_file(fname, as_attachment=True, attachment_filename=fname)
#     else:
#         return redirect(url_for('home_page'))
    

# @app.route('/download_specific/<rollno>')
# def download_specific(rollno):
#     if 'user' in session.keys():

#         conn = sqlite3.connect('data.db')
#         cursor = conn.execute(f"SELECT NAME, ID, DESIGNATION, DAY, MONTH, YEAR, LOGIN_TIME from ATTENDANCE where ID = '{rollno}' ")
#         attendance_list = []
#         for row in cursor:
#             attendance_list.append(row)
#         conn.close()
        
#         name = []
#         rollnox = []
#         designation = []
#         date = []
#         login_time = []
        
#         for i in attendance_list:
#             name.append(i[0])
#             rollnox.append(i[1])
#             designation.append(i[2])
#             date.append(f"{i[3]}-{i[4]}-{i[5]}")
#             login_time.append(i[6])

#         data = pd.DataFrame({'Name': name, 'ID': rollnox, 'Designation': designation, 'Date': date, 'Login_Time': login_time})
#         fname = "Attendance_"+str(rollno)+'_download.csv'
#         data.to_csv(fname, index=False)
#         return send_file(fname, as_attachment=True, attachment_filename=fname)
#     else:
#         return redirect(url_for('home_page'))



app.secret_key = 'q12q3q4e5g5htrh@werwer15454'

if __name__ == '__main__':
    app.jinja_env.globals.update(enumerate=enumerate, len = len)
    app.run(host='0.0.0.0', port= 5000, debug=True)#80)
# global outputFrame ## Warning: Unused global
