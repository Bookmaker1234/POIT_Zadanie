from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import time
import MySQLdb
import configparser as ConfigParser
import random
import math
import serial
import json
global s

async_mode = None

app = Flask(__name__)


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')
print(myhost)

def background_thread(args):
    count = 0
    dataCounter = 0
    global A
    global D
    global b
    b = 2
    D = 0
    A = 1
    dataList = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)          
    global s
    s = 2
    while True:
#             if args:
#               A = dict(args).get('A')
#             else:
#               A = 100
            
        
            if b == 1:
                ser = serial.Serial("/dev/ttyS0")
                ser.baudrate = 9600
                socketio.sleep(1)
                count += 1
            elif b == 0:
                ser.close()
            while (s == 1):
                if b == 2:
                    s = 0
                else:
                    count += 1
                    dataCounter +=1
                    read_ser = ser.readline()
                    premenna = read_ser.decode().replace("\r\n","").split(",")
                    teplota = premenna[0]
                    vlhkost = premenna[1]
                    if float(A) >= float (vlhkost):
                        kontrola = "Je tu vysoka vlhkost"
                        
                    if s == 1:
                        dataDict = {
                            "t": time.time(),
                            "x": dataCounter,
                            "teplota": teplota,
                            "vlhkost": vlhkost}
                        dataList.append(dataDict)
                    elif s == 0:
                        if len(dataList)>0:
                            print(str(dataList))
                            fuj = str(dataList).replace("'", "\"")
                            print(fuj)
                            fo = open("static/zapisovanie/databaza.txt","a+")
                            fo.write("%s\r\n" %fuj)
                            fo.close()
                            cursor = db.cursor()
                            cursor.execute("SELECT MAX(id) FROM merania")
                            maxid = cursor.fetchone()
                            cursor.execute("INSERT INTO merania (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, fuj))
                            db.commit()
                        
                        dataList = []
                        dataCounter = 0
                    if float (A) >= float (vlhkost):
                        socketio.emit('my_response',
                                  {'data': json.dumps({"vlhkost": kontrola}), 'count': count},
                                  namespace='/test')
                     
                    socketio.emit('my_response',
                          {'data': json.dumps({"teplota": teplota,"vlhkost": vlhkost,"argument": float (A)}), 'count': count},
                          namespace='/test')
                    
                    socketio.emit('my_response2',
                          {'data': teplota,'data1': vlhkost,'count': count},
                          namespace='/test')
                    
                    socketio.emit('my_response3',
                          {'data': teplota,'data1': vlhkost, 'count': count},
                          namespace='/test')
    #                 if float(D) >= 1:
    #                     socketio.emit('my_response4',
    #                           {'data': float (D), 'count': count},
    #                           namespace='/test')
            else:
                socketio.sleep()
                
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/citanie')
def readall():
    fo = open("static/zapisovanie/databaza.txt","r")
    rows = fo.readlines()
    return json.dumps(rows)

@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1
    global A
    A = message['value']    
    emit('my_response',
         {'data': message['value'], 'count': session['receive_count']})

# @socketio.on('my_event1', namespace='/test')
# def test_message1(message):   
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     global D
#     D = message['value']    
#     emit('my_response',
#          {'data': message['value'], 'count': session['receive_count']})

@socketio.on('Begin_request', namespace='/test')
def Begin_request():
    global b
    print('Begin', request.sid)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Begin!', 'count': session['receive_count']})
    b = 1
    
@socketio.on('End_request', namespace='/test')
def End_request():
    global b
    print('End', request.sid)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'End!', 'count': session['receive_count']})
    b = 0

@socketio.on('start_request', namespace='/test')
def start_request():
    global s
    print('Start', request.sid)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Start!', 'count': session['receive_count']})
    s = 1

@socketio.on('click_eventStart', namespace='/test')
def db_message(message):
    session['btn_value'] = 1
    
@socketio.on('click_eventStop', namespace='/test')
def db_message(message):
    session['btn_value'] = 0
    
@socketio.on('stop_request', namespace='/test')
def stop_request():
    global s
    s = 0
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Stop!', 'count': session['receive_count']})
    

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()
    
@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
    emit('my_response', {'data': 'Connected', 'count': 0})

@app.route('/read/<string:num>')
def readmyfile(num):
    fo = open("static/zapisovanie/databaza.txt","r")
    rows = fo.readlines()
    return rows[int(num)-1]

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)
    
@socketio.on('start', namespace='/test')
def test_start():
    print('Start', request.sid)

@socketio.on('stop', namespace='/test')
def test_stop():
    print('Stop', request.sid)
    

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)

