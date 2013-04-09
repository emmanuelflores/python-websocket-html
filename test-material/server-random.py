import SocketServer
import json
import random

class testValue():
	def getValue(self):
		val = random.random()
		return round(val,2) 

class MyTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True


class MyTCPServerHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            data = json.loads(self.request.recv(1024).strip())
            # process the data, i.e. print it:
            print data
            # send some 'ok' back
            t = testValue()
            self.request.sendall(json.dumps({'value':str(t.getValue())}))
        except Exception, e:
            print "Exception wile receiving message: ", e

server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
server.serve_forever() 