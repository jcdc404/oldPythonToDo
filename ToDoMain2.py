import bottle, json, random, hashlib, sqlite3, cherrypy, jinja2, binascii
from bottle import request, response, route, run, get, post, static_file, redirect, template
from os import urandom
import time

home = "/home/leppie/Bottle_Projects"

@route('/<filepath:path>')
def send_static(filepath):
	return static_file(filepath, root=home)

@route('/scripts/<filepath:path>')
def send_static(filepath):
	return static_file(filepath, root=home)

@route('/templates/<filepath:path>')
def send_static(filepath):
	return static_file(filepath, root=home)

@post('/ToDoPage', method='post')
def index1():
	user = ckCookie("Username")
	for key in request.headers:
		print (key, ": ", request.headers[key])
	try:
		body = json.loads(request.body.getvalue())
		print ("Post Body: ",body)
		try:
			if body["newtask"]:
				print (body["newtask"])
		except KeyError:
			pass
		try:
			if body["newitem"]:
				insertIntoDb("Items", body["newitem"], "db.db", time.ctime())
				data = dbSelectAll("db.db")
				return json.dumps(data)
		except KeyError:
			pass
		try:
			if body["markitemComp"]:
				print (body)
				dbUpdate2(
					'UPDATE Items SET Status = "complete" WHERE Username = ? AND "DateCreated" = ? AND "Text" = ?', 
					(body["markitemComp"]["user"], body["markitemComp"]["timecreated"], body["markitemComp"]["text"] )
					)
				data = dbSelectAll("db.db")
				return json.dumps(data)
		except KeyError:
			pass
		try:
			if body["markitemInComp"]:
				print (body)
				dbUpdate2(
					'UPDATE Items SET Status = ? WHERE Username = ? AND "DateCreated" = ? AND "Text" = ?', 
					(None,body["markitemInComp"]["user"], body["markitemInComp"]["timecreated"], body["markitemInComp"]["text"] )
					)
				data = dbSelectAll("db.db")
				return json.dumps(data)
		except KeyError:
			pass
		try:
			if body["deletecookies"] == "deletecookies":
				response.delete_cookie("Token")
				response.delete_cookie("Username")
				dbUpdate("users", "Token", "Username", None, user,"db.db")
				redirect('/')
		except KeyError:
			pass
		try:
			if body["delete"]:
				print (body)
				dbDelete2(
					'DELETE FROM Items WHERE Username = ? AND DateCreated = ? AND "Text" = ?', 
					(body["delete"]["user"], body["delete"]["timecreated"], body["delete"]["text"])
					)
				data = dbSelectAll("db.db")
				return json.dumps(data)
		except KeyError:
			pass
	except KeyError:
		pass
	
@get('/ToDoPage')
def index():
	for key in request.headers:
		print (key, ": ", request.headers[key])
	try:
		body = json.loads(request.body.getvalue())
		print ("Get Body: "+body)
	except ValueError:
		body = request.body.getvalue()
		print ("Get Body: "+body)
	if not isLoggedIn():
		redirect('/')
	else:
		return static_file('ToDoPage.html', root=home)


@get('/')
def index():
	if isLoggedIn():
		redirect("/ToDoPage")
	else:
		index = static_file('LoginTemplate.html', home)
		return index

@post('/', method='post')
def index():
	if not isLoggedIn():
		user = request.forms.get("username")
		password = request.forms.get("password")
		salt = dbSelectOne("salt","Users","Username",user,"db.db")
		if salt == None:
			salt="xxxx"
		hashed = hashlib.sha512(user+password+salt).hexdigest()
		if not dbSelectOne("hash","Users","Username",user,"db.db"):
			redirect('/')
		if hashed == dbSelectOne("hash","Users","Username",user,"db.db"):
			print ("User can be logged in")
			token = setToken(user)
			dbUpdate("users", "Token", "Username",token, user, "db.db")
		redirect('/')
	else:
		redirect('/ToDoPage')


def setToken(username):
	token = makeToken()
	response.set_cookie("Username",username,max_age=300)
	response.set_cookie("Token",token,max_age=300, )
	return token

def isLoggedIn():
	print ("Attempting to Login")
	if  not ckCookie("Username"):
		return False
	if  not ckCookie("Token"):
		return False
	user = ckCookie("Username")
	cookie_token = ckCookie("Token")
	if dbSelectOne("Token","Users","Username",user,"db.db") == cookie_token:
		return (True)
	else:
		return (False)

def dbSelectOne(getfield,table,matchfield,matchdata,db):
	#connect, make cursor, select, fetchall, close-connection, return data
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('SELECT %s FROM %s WHERE %s = ?' % (getfield,table,matchfield),(matchdata,))
	data = c.fetchone()
	c.connection.close()
	if data == None:
		return data
	return str(data[0])

@post('/getContent', method='post')
def index():
	data = dbSelectAll("db.db")
	return json.dumps(data)


def dbSelectAll(db):
	user = request.get_cookie("Username")
	print (user)
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('SELECT * FROM "Items" WHERE "Username" = ?', (user,))
	data = c.fetchall()
	c.connection.close()
	print (data)
	return data

def dbUpdate(table, updatefield,matchfield,newvalue,matchvalue, db):
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('UPDATE %s SET %s = ? WHERE %s = ?'%(table, updatefield, matchfield), (newvalue, matchvalue))
	print ("dbUpdated")
	conn.commit()
	c.connection.close()
	
def dbUpdate2(execStr, opts):
	## UPDATE table SET field = ? WHERE value = ? AND value = ?, (value1, value2, value3)
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute(execStr,opts)
	print ("dbUpdated")
	conn.commit()
	c.connection.close()

def dbDelete2(execStr, opts):
	## DELETE FROM table WHERE value = ? AND value = ?, (value1, value2, value3)
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute(execStr,opts)
	print ("dbUpdated")
	conn.commit()
	c.connection.close()

def ckCookie(cookie):
	if type(request.get_cookie(cookie))== None:
		return False
	else:
		return request.get_cookie(cookie)

def makeToken():
	randnum = urandom(128)
	token = binascii.hexlify(randnum)
	return str(token).upper()

def insertIntoDb(table, text, database, DateCreated, dueDate=None):
	''' Inserts one row into the table. Columns can be a tuple. '''
	conn = sqlite3.connect(database)
	c = conn.cursor()
	user = ckCookie("Username")
	try:
		c.execute('INSERT INTO %s VALUES (?,?,?,?,?)'%(table),(text,user,None,DateCreated,dueDate))
	except Exception as e:
		raise e
	data = c.fetchall()
	c.connection.commit()
	conn.close()
	return data


run(host='localhost', port=8080)