from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import time
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

def background_thread(args):
    count = 0
    global s
    s = 2
    while True:
           # if args:
           #   A = dict(args).get('A')
         #   else:
         #     A = 1
        
        #print (A)
        #print args
            if s == 1:
                ser = serial.Serial("/dev/ttyS0")
                ser.baudrate = 9600
                socketio.sleep(1)
                count += 1
            while (s == 1):
                count += 1
                read_ser = ser.readline()
                premenna = read_ser.decode().replace("\r\n","").split(",")
                teplota = premenna[0]
                vlhkost = premenna[1]
                
                dataDict= {
                    "x": count,
                    "teplota":teplota,
                    "vlhkost":vlhkost
                    }
                
               # dataList.append(dataDict)
                
                
                socketio.emit('my_response',
                              {'data': json.dumps({"teplota": teplota,"vlhkost": vlhkost}), 'count': count},
                              namespace='/test')
                socketio.emit('my_response2',
                      {'data': teplota,'data1': vlhkost,'count': count},
                      namespace='/test')
                
                socketio.emit('my_response3',
                      {'data': teplota,'data1': vlhkost, 'count': count},
                      namespace='/test')
            else:
                socketio.sleep()
                
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
  
@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
    emit('my_response',
         {'data': message['value'], 'count': session['receive_count']})

@socketio.on('start_request', namespace='/test')
def start_request():
    global s
    print('Start', request.sid)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Start!', 'count': session['receive_count']})
    s = 1
    
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