# import random
# import simplejson

# def generate_random():
# 	val = random.random()
# 	return round(val,2)

# print generate_random()
# print generate_random()

#http://www.ryannedolan.info/teaching/cs4830/examples/python-examples

from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json

me = {"name": "emmnuel"}

class MyRequestHandler (BaseHTTPRequestHandler) :

    def do_GET(self) :

        if self.path == "/me" :
            #send response code:
            self.send_response(200)
            #send headers:
            self.send_header("Content-type:", "text/html")
            # send a blank line to end headers:
            self.wfile.write("\n")

            #send response:
            json.dump(me, self.wfile)

server = HTTPServer(("localhost", 8000), MyRequestHandler)

server.serve_forever()