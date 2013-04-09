import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def is_even(n):
	return n%2 == 0

def twoArguments(n1, n2):
	return n1 + n2

def helloStefan():
	return 10

def helloBitches():
	return  "hello helloBitches!!!"


server = SimpleXMLRPCServer(("localhost",8000))
print "Listening to port 8000..."
server.register_function(is_even,"is_even")
server.register_function(helloStefan,"helloStefan")
server.register_function(helloBitches,"helloBitches")
server.serve_forever()