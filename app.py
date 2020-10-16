from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import logging
from logging.handlers import RotatingFileHandler
from random import *

app=Flask(__name__)
app.secret_key=b'thisisthesecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'
db = SQLAlchemy(app)


@app.route('/')
def index():
	app.logger.info(session.get('username'))
	app.logger.info(session.get('usertype'))
	app.logger.info(session.get('sid'))
	if 'username' in session:
		if session.get('usertype') == 'student':
			return render_template('student.html', name=session.get('username'))
		
		elif session.get('usertype') == 'instructor':
			sql1 = """SELECT * FROM marks"""
			results = db.engine.execute(text(sql1))
			return render_template('instructor.html', name=session.get('username'), data=results)		
	return render_template('warnings.html', warning='notlogin')


@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':

		# Check the type of user to decide which table should be used
		if request.form['type'] == 'student':
			sql = """
				SELECT *
				FROM students
			"""
		elif request.form['type'] == 'instructor':
			sql = """
				SELECT *
				FROM instructors
			"""
		results = db.engine.execute(text(sql))

		for result in results:
			if result['username']==request.form['username'] and result['password']==request.form['password']:
				# Set the user name of the session
				session['username']=request.form['username']
				# Set the type of the user
				if request.form['type'] == 'student':
					session['usertype'] = 'student'
				elif request.form['type'] == 'instructor':
					session['usertype'] = 'instructor'
				
				# Direct to the success log in page	
				return redirect(url_for('index'))
		return render_template('warnings.html', warning='incorrectlogin')
	
	elif 'username' in session:
		return redirect(url_for('index'))
	
	else:
		return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():
	if request.method == 'POST':

		lastname=request.form['last']
		firstname=request.form['first']
		username=request.form['username']
		password=request.form['password']
		sid=randint(100000, 999999)
		tid=randint(100, 999)
		
		# Check if each box was filled in
		if lastname=="" or firstname=="" or username=="" or password=="":
			return render_template('warnings.html', warning='emptyInput')

		if request.form['type'] == 'student':
			sql = """SELECT *
					FROM students"""
			results = db.engine.execute(text(sql))

			# Check whether this username is already in the database
			# If exist, return a message telling that the user exist
			for result in results:
				if result['username'] == username:
					return render_template('warnings.html', warning='userexist')

			# When proceed to this point, this mean that no such user in 
			# the database, we can insert this new user to the table 'students'
			updateSQL="""INSERT INTO students(username, password, firstName, lastName, SID)
				   VALUES ('{}', '{}', '{}', '{}','{}')
				   """.format(username, password, firstname, lastname, sid)
			db.engine.execute(text(updateSQL))
			# Insert SID to the table marks
			updateSQL="""INSERT INTO marks(SID, firstName, lastName) VALUES ('{}')""".format(sid, firstname, lastname)
			db.engine.execute(text(updateSQL))
			
		elif request.form['type'] == 'instructor':
			sql = """SELECT username FROM instructors"""
			results = db.engine.execute(text(sql))

			# Check whether this username is already in the database
			# If exist, return a message telling that the user exist
			for user in results:
				if user == username:
					return "This user already exist!"

			updateSQL="""INSERT INTO instructors(username, password, firstName, lastName, TID)
				   VALUES ('{}', '{}', '{}', '{}', '{}')
				   """.format(username, password, firstname, lastname, tid)
			db.engine.execute(text(updateSQL))

		return render_template('warnings.html', warning='registerSuccess')
	
	else:
		return render_template('register.html')

@app.route('/student/grades')
def grades():
	if session.get('username') == None:
		return redirect(url_for('index'))
		
	mark_sql = """
				SELECT *
				FROM marks 
				WHERE username = "%s"
	""" % (session.get('username'))
	
	remark_sql = """
				SELECT *
				FROM remark 
				WHERE username = "%s"
	""" % (session.get('username'))
	
	
	mark_results = db.engine.execute(text(mark_sql)).fetchone()
	remark_results = db.engine.execute(text(remark_sql)).fetchone()
	
	grade_records = {}
	remark_request = {}
	
	for key in mark_results.keys():
		if not key == 'SID':  
			grade_records[key] = mark_results[key]
		
	for key in remark_results.keys():
		if not key == 'SID':  
			remark_request[key] = remark_results[key]
		
	return render_template('grades.html', name=session.get('username'), marks=grade_records, request=remark_request)
	
	
@app.route('/grade/handdle_request', methods=['GET', 'POST'])
def handdle_request():
	if 'username' in session:
		explain = request.form['explain']
		field = request.form['field']
		
		sql = '''
			UPDATE remark
			SET %s='%s'
			WHERE username = '%s'
		''' % (field, explain,session.get('username') )
		
		db.engine.execute(text(sql))
		
		return redirect(url_for('grades'))
	
	else:
		return redirect(url_for('login'))
	

@app.route('/student/feedback')
def feedback():
	if 'username' in session and session.get('usertype') == 'student':
		sql = '''
			SELECT firstName, lastName, TID 
			FROM instructors
		'''
		results = db.engine.execute(text(sql))
		
		instructor_info = {}
		
		for result in results:
			full_name = result['firstName'] + " " + result['lastName']
			instructor_info[result['TID']] = full_name
		
		return render_template('feedback.html', name=session.get('username'), instructor_info=instructor_info)
	else:
		return redirect(url_for('login'))

	
@app.route('/grade/handdle_feedback', methods=['GET','POST'])
def handdle_feedback():
	if 'username' in session and session.get('usertype') == 'student':
		tid = request.form['tid']
		recommend_l = request.form['recommend_l']
		recommend_t = request.form['recommend_t']
		like_l = request.form['like_l']
		like_t = request.form['like_t']
		
		sql = '''
			INSERT INTO feedback
			(TID, like_t, recommend_t, like_l, recommend_l)
			VALUES
			('%s', '%s', '%s', '%s', '%s')
		''' % (tid, like_t, recommend_t, like_l, recommend_l)
		
		db.engine.execute(text(sql))
		
		return redirect(url_for('feedback'))
	else:
		return redirect(url_for('login'))


@app.route('/instructor/editmark', methods=['GET','POST'])
def editmark():
	if 'username' in session:
		if request.method == 'POST':
			q1=request.form['quiz1']
			q2=request.form['quiz2']
			q3=request.form['quiz3']
			midterm=request.form['mid']
			a1=request.form['a1']
			a2=request.form['a2']
			sid = request.form['sid']

			# Check if the student ID is valid
			if not sid.isalnum() or not len(sid) == 6:
				return render_template('warnings.html', warning='invalidID')

			# Check if the inputs are numbers
			if q1.isalnum() and q2.isalnum() and q3.isalnum() and midterm.isalnum() and\
				a1.isalnum() and a2.isalnum():
				updateSQL="""UPDATE marks
						SET quiz1 = '{}', quiz2 = '{}', quiz3 = '{}',midterm = '{}', a1 = '{}', a2 = '{}'  
						WHERE SID = '{}'""".format(q1, q2, q3, midterm, a1, a2, sid)
				db.engine.execute(text(updateSQL))
				return redirect(url_for('login'))
			else:
				return render_template('warnings.html', warning='notInt')
	
		else:
			return render_template('edit.html')
	
	else:
		return redirect(url_for('index'))


@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('login'))


@app.route('/announcement')
def announcement():
	if 'username' in session:
		return render_template('announcement.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/assignment')
def assignment():
	if 'username' in session:
		return render_template('assignment.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/calendar')
def calendar():
	if 'username' in session:
		return render_template('calendar.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/course_team')
def course_team():
	if 'username' in session:
		return render_template('course_team.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/instructor/feedback')
def ifeedback():
	app.logger.info(session.get('username'))
	if 'username' in session:
		if session.get('usertype') == 'instructor':
			sql1 = """
					SELECT * 
					FROM feedback
					"""
			results = db.engine.execute(text(sql1))
			return render_template('ifeedback.html', data=results)		
	return render_template('warnings.html', warning='notlogin')



@app.route('/lab')
def lab():
	if 'username' in session:
		return render_template('lab.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/lecture')
def lecture():
	if 'username' in session:
		return render_template('lecture.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/resources')
def resources():
	if 'username' in session:
		return render_template('resources.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/tests')
def tests():
	if 'username' in session:
		return render_template('tests.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/index')
def home():
	if 'username' in session:
		return render_template('index.html')
	return render_template('warnings.html', warning='notlogin')

@app.route('/instructor/remark')
def iremark():
	if 'username' in session:
		if session.get('usertype') == 'instructor':
			sql1 = """
					SELECT * 
					FROM remark
					"""
			results = db.engine.execute(text(sql1))
			return render_template('iremark.html', data=results)		
	return render_template('warnings.html', warning='notlogin')

@app.route('/instructor/view_grades')
def igrades():
	if 'username' in session:
		if session.get('usertype') == 'instructor':
			sql1 = """
					SELECT * 
					FROM marks
					"""
			results = db.engine.execute(text(sql1))
			return render_template('igrades.html', data=results)		
	return render_template('warnings.html', warning='notlogin')


if __name__=="__main__":
	app.run(debug=True, host='localhost')