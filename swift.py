# SWIFT Taskbook
# Web Application for Task Management

# system libraries
import os

# web transaction objects
from bottle import request, response

# HTML request types
from bottle import route, get, put, post, delete

# web page template processor
from bottle import template

#database library & support
import dataset
from random import seed, randint
import time

VERSION=0.1

# development server
PYTHONANYWHERE = ("PYTHONANYWHERE_SITE" in os.environ)

if PYTHONANYWHERE:
    from bottle import default_app
else:
    from bottle import run

# ---------------------------
# Session database
# ---------------------------

session_db = dataset.connect('sqlite:///session.db')
seed()

# ---------------------------
# web application routes
# ---------------------------

@route('/')
@route('/tasks')
def tasks():
    session_id = request.cookies.get('session_id',None)
    print("session_id in request = ",session_id)
    if session_id:
        session_id = int(session_id)
    else:
        session_id = randint(10000000, 20000000)
    # try to load session information
    session_table = session_db.create_table('session')
    sessions = list(session_table.find(session_id=session_id))
    if len(sessions) == 0:
        # we need to create a session
        session = {
                    "session_id":session_id,
                    "started_at":time.time()
                  }
        # put the session in the database
        session_table.insert(session)
    else:
        session = sessions[0]
    # update the session
    if "visits" in session:
        session['visits'] = session['visits'] + 1
    else:
        session['visits'] = 1
    print(session)
    # persist the session
    session_table.update(row=session, keys=['session_id'])

    response.set_cookie('session_id',str(session_id))
    print("session_id send in response = ",str(session_id))
    return template("tasks.tpl")


@route('/session')
def tasks():
    session_id = request.cookies.get('session_id',None)
    print("session_id in request = ",session_id)
    if session_id:
        session_id = int(session_id)
        session_table = session_db.create_table('session')
        sessions = list(session_table.find(session_id=session_id))
        if len(list(sessions)) > 0:
            session = sessions[0]
        else:
            session = {}
    else:
        session = {}
    response.set_cookie('session_id',str(session_id))
    return template("session.tpl",session_str=str(dict(session)))

@route('/login/<user>')
def login(user):
    username = user
    print(username)
    session_id = request.cookies.get('session_id',None)
    print("session_id in request = ",session_id)
    if session_id:
        session_id = int(session_id)
    else:
        session_id = randint(10000000, 20000000)
    # try to load session information
    session_table = session_db.create_table('session')
    sessions = list(session_table.find(session_id=session_id))
    if len(sessions) == 0:
        # we need to create a session
        session = {
                    "session_id":session_id,
                    "started_at":time.time()
                  }
        # put the session in the database
        session_table.insert(session)
    else:
        session = sessions[0]
    # update the session
    session['username'] = username
    print(session)
    # persist the session
    session_table.update(row=session, keys=['session_id'])
    return template("login.tpl")

@route('/register')
def login():
    return template("register.tpl")

# ---------------------------
# task REST api
# ---------------------------

import json
import dataset
import time

taskbook_db = dataset.connect('sqlite:///taskbook.db')

@get('/api/version')
def get_version():
    return { "version":VERSION }

@get('/api/tasks')
def get_tasks():
    'return a list of tasks sorted by submit/modify time'
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    task_table = taskbook_db.get_table('task')
    tasks = [dict(x) for x in task_table.find(order_by='time')]
    return { "tasks": tasks }

@post('/api/tasks')
def create_task():
    'create a new task in the database'
    try:
        data = request.json
        for key in data.keys():
            assert key in ["description","list"], f"Illegal key '{key}'"
        assert type(data['description']) is str, "Description is not a string."
        assert len(data['description'].strip()) > 0, "Description is length zero."
        assert data['list'] in ["today","tomorrow"], "List must be 'today' or 'tomorrow'"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    try:
        task_table = taskbook_db.get_table('task')
        task_table.insert({
            "time": time.time(),
            "description":data['description'].strip(),
            "list":data['list'],
            "completed":False
        })
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status':200, 'success': True})

@put('/api/tasks')
def update_task():
    'update properties of an existing task in the database'
    try:
        data = request.json
        for key in data.keys():
            assert key in ["id","description","completed","list"], f"Illegal key '{key}'"
        assert type(data['id']) is int, f"id '{id}' is not int"
        if "description" in request:
            assert type(data['description']) is str, "Description is not a string."
            assert len(data['description'].strip()) > 0, "Description is length zero."
        if "completed" in request:
            assert type(data['completed']) is bool, "Completed is not a bool."
        if "list" in request:
            assert data['list'] in ["today","tomorrow"], "List must be 'today' or 'tomorrow'"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    if 'list' in data:
        data['time'] = time.time()
    try:
        task_table = taskbook_db.get_table('task')
        task_table.update(row=data, keys=['id'])
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
        return
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status':200, 'success': True})

@delete('/api/tasks')
def delete_task():
    'delete an existing task in the database'
    try:
        data = request.json
        assert type(data['id']) is int, f"id '{id}' is not int"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    try:
        task_table = taskbook_db.get_table('task')
        task_table.delete(id=data['id'])
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
        return
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'success': True})

if PYTHONANYWHERE:
    application = default_app()
else:
   if __name__ == "__main__":
       run(host='localhost', port=8080, debug=True)