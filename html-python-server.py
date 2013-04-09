import base64
import hashlib
import json
import os
import socket
import struct
import sys
import threading
import time
import traceback
import urllib
import urllib2

import random

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

#html client
#go to http://localhost:8080/
CLIENT = """
<!DOCTYPE html>
<html>
	<meta charset = "UTF-8">
	<title>Streamer</title>
	<head>
	<script type="text/javascript">
function diy(callback){
  window.setTimeout(callback, 1000 / 30);
}

function aggregate(callback){
  return window.requestAnimationFrame       ||
         window.webkitRequestAnimationFrame ||
         window.mozRequestAnimationFrame    ||
         window.oRequestAnimationFrame      ||
         window.msRequestAnimationFrame     ||
         diy;
}

window.animate = (aggregate)();


function draw(){  
  var canvas = document.getElementById("canvas");
  animate(draw);
 }

var samples = [];

//parse the JSON
function enqueue(data){
  data = JSON.parse(data);
  data.shift()
  samples.push(data);
  if(samples.length > 2048){
    samples.shift();
  }
}

function go(){
  draw();
  if("WebSocket" in window){
    var ws = new WebSocket("ws://" + document.domain + ":9090/");
    console.log(ws);
    ws.onopen    = function(){ console.log("Stream open"); }
    //ws.onmessage = function(event){ enqueue(event.data); }
    //ws.onmessage = function(event){console.log(event); }
    ws.onmessage = function(event){
    	console.log(event);
    	console.log(JSON.parse(event.data));
        }
    ws.onclose   = function(){ console.log("Stream close"); }
  }
}

  </script>
</head>
<body onload="go();" style="width:100%; height:100%; margin:0px;"><canvas id="canvas" width="100%" height="100%"/></body>
</html>
"""

#python
"""
Stoppable web server.
"""
class StoppableHTTPServer(HTTPServer):
    """
    Main loop of the server.
    Method called internally by the HTTP Python library
    standard implementation is an infinite loop but this implementation depends on the field stop.
    """
    def serve_forever(self):
        self.stop = False
        while not self.stop:
            self.handle_request()

"""
An object of this class is created to handle a single web connection and HTTP request.
"""
class WebHandler(BaseHTTPRequestHandler):
    """
    Default one prints every request to the console.
    This one does not do anything (and effectively suppresses unwanted messages printed to the console).
    """
    def log_request(self, code='-', size='-'):
        return

    """
    The method handling the HTTP request.
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', '%d' % len(CLIENT))
        self.end_headers()
        self.wfile.write(CLIENT)
        #file = open('streamer.html', 'rb')
        #try:
        #    self.send_response(200)
        #    self.send_header('Content-Type', 'text/html')
        #    file.seek(0, os.SEEK_END)
        #    length = file.tell()
        #    file.seek(0, os.SEEK_SET)
        #    self.send_header('Content-Length', '%d' % length)
        #    self.end_headers()
        #    while True:
        #        buffer = file.read(20 * 1024)
        #        if len(buffer) == 0:
        #            break
        #        self.wfile.write(buffer)
        #except Exception, exception:
        #    self.send_response(500)
        #file.close()

class WebServer(threading.Thread):#create the web server
    """
    Use this method to start the web server.
    It connects the listening socket and starts the main dispatcher thread.
    """
    def open(self):
        self.server = StoppableHTTPServer(('', 8080), WebHandler)
        self.start()#start webserver

    """
    Web server thread method. While the indicator of operation
    is on it accepts to incoming connections and creates a handler thread.
    """
    def run(self):
        self.server.serve_forever()#keep the server running

    """
    Use this method to stop the web server.
    It disconnects the socket and then closes the channel.
    """
    def close(self):
        self.server.stop = True
        self.server.socket.close()

def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # try:
    #     s.connect(("gmail.com",80))
    #     result = s.getsockname()[0]
    # except:
    result = '127.0.0.1'
    s.close()
    return result


class WebSocket(threading.Thread):
    def open(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("", 9090))
        self.server.listen(5)
        self.HANDSHAKE_SAFARI = 'HTTP/1.1 101 Web Socket Protocol Handshake\r\nUpgrade: WebSocket\r\nConnection: Upgrade\r\nSec-WebSocket-Origin: http://%s:8080\r\nSec-WebSocket-Location: ws://%s:9090/\r\n\r\n'
        self.HANDSHAKE_SAFARI = self.HANDSHAKE_SAFARI % (ip(), ip())
        self.HANDSHAKE = 'HTTP/1.1 101 Web Socket Protocol Handshake\r\nUpgrade: WebSocket\r\nConnection: Upgrade\r\nSec-WebSocket-Origin: http://%s:8080\r\nSec-WebSocket-Location: ws://%s:9090/\r\nSec-WebSocket-Accept: %s\r\n\r\n'
        self.HANDSHAKE = self.HANDSHAKE % (ip(), ip(), '%s')
        self.KEY = 'WebSocket-Key: '
        self.GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11' # '46a458b0-fed5-4a91-8911-6f2ca3981afb'
        self.stop = False
        self.client = None
        self.start()

    def process(self, message):
        headers = {}
        (header, data) = message.split('\r\n\r\n', 1)
        for line in header.split('\r\n')[1:]:
            (key, value) = line.split(": ", 1)
            headers[key] = value
        return (headers, data)

    def run(self):
        while not self.stop:
            try:
                client, address = self.server.accept()
            except:
                continue
            handshaken = False
            message = ''
            try:
                while not handshaken and not self.stop:
                    message += client.recv(1024)
                    if message.find('\r\n\r\n') != -1:
                        (headers, data) = self.process(message)
                        if not headers.has_key('Sec-WebSocket-Key1') or len(data) >= 8:
                            handshaken = True
                        else:
                            continue
                        if headers.has_key('Sec-WebSocket-Key1'):
                            self.safari = True
                            key1 = headers['Sec-WebSocket-Key1']
                            key2 = headers['Sec-WebSocket-Key2']
                            key3 = data[:8]
                            handshake = self.HANDSHAKE_SAFARI
                            num1 = int(''.join([digit for digit in list(key1) if digit.isdigit()]))
                            spaces1 = len([char for char in list(key1) if char == ' '])
                            num2 = int(''.join([digit for digit in list(key2) if digit.isdigit()]))
                            spaces2 = len([char for char in list(key2) if char == ' '])
                            combined = struct.pack('>II', num1/spaces1, num2/spaces2) + key3
                            token = hashlib.md5(combined).digest()
                            handshake += token
                        else:
                            self.safari = False
                            key = headers['Sec-WebSocket-Key']
                            key = hashlib.sha1(key + self.GUID).digest()
                            handshake = self.HANDSHAKE % base64.b64encode(key)
                        client.send(handshake)
                        self.client = client
            except Exception, exception:
                print traceback.format_exc()


    def post(self, message):
        if self.client != None:
            try:
                if self.safari:
                    self.client.send('\x00%s\xFF' % message)
                else:
                    length = len(message)
                    if length <= 125:
                        #The first byte 0x81 means that this is the final (and only) frame of this message (i.e. no fragmentation).
                        prefix = '\x81%c' % chr(length) 
                    else:
                        prefix = '\x81%c%c%c' % (chr(126), chr(length >> 8), chr(length & 0xFF))
                    self.client.send(prefix + message)
            except:
                return

    def close(self):
        self.stop = True
        self.server.close()


def textual(sample):
    if None in sample:
        return None
    else:
        line = ''
        for value in sample:
            if line != '':
                line += ','
            line += '%d' % value
        return line


def post(message):
	length = len(message)
	if length <= 125:
		prefix = '\x81%c' % chr(length)
	else:
		prefix = '\x81%c%c%c' % (chr(126), chr(length >> 8), chr(length & 0xFF))

	return prefix + message        


def createSampleArray(sample):
	sample[0] = random.randint(1,100)
	sample[1] = random.randint(1,100)
	sample[2] = random.randint(1,100)
	print sample
	return sample



def streamTest():
	sample = [None, None, None]
	timestamp = random.randint(1,1000)
	line = textual(createSampleArray(sample))
	line = '[%d,%s]' % (timestamp, line)
	#print ("Sending to socket: " + line + "\n")
	#print ("fake post values: "+ post(line))

# def stream():
# 	sample = [None, None, None]
# 	timestamp = random.randint(1,1000)
# 	then = 0
# 	try:
# 		print ("hello")

def stream():
	sample = [None, None, None]
	timestamp = random.randint(1,1000)
	then = 0
	buffer = ' '
	server = WebServer()
	server.open()
	streamer = WebSocket()
	streamer.open()
	time.sleep(2)
	while(True):
		# timestamp = random.randint(1,1000)
		# line = textual(createSampleArray(sample))
		# line = '[%d,%s]' % (timestamp, line)
		# streamer.post(line)
		#line = {'channel1': 30}
		line = {'ch1':random.randint(1,1000), 'ch2':random.randint(1,1000)}
		print (line)
		streamer.post(json.dumps(line))
		time.sleep(1)
	# try:
	# 	line = textual(createSampleArray(sample))
	# 	line = '[%d,%s]' % (timestamp, line)
	# 	streamer.post(line)
	# except Exception, exception:
	# 	#print.traceback.format_exc()
	# 	time.sleep(2)
	# 	server.close();
	choice = raw_input('Stop device (S)\n')
	if choice in 'Ss':
		server.close()
	# if choice in 'Tt':
	# 	timestamp = random.randint(1,1000)
	# 	line = textual(createSampleArray(sample))
	# 	line = '[%d,%s]' % (timestamp, line)
	# 	streamer.post(line)

def main():
	stream()
	# try:
	# 	stream()
	# except Exception, exception:
	# 	print traceback.format_exc()
	# raw_input('Press Enter to quit')

if __name__ == "__main__":
    main()
