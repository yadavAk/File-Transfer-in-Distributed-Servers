import socket
import sys
import csv
from _thread import *

rtl_file = open('localhost.rtl', 'r')
lines = rtl_file.readlines()

for line in lines:
	words = line.split('|')
	try:
		if(words[0].strip() == 'B'):
			HOST = words[1].strip()
			PORT = int(words[2].strip())
	except ValueError:
		print('Something went wrong while parsing data from routing table file. Exiting...')
		sys.exit()


# HOST = ""  # Symbolic name meaning all available interfaces
# PORT = 8002	# int(input('Enter Arbitrary non-privileged port no. :'))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print("Bind failed. Error code : " + str(msg[0]) + " Message " + msg[1])
    sys.exit()

print("Socket bind complete")


s.listen(10)
# The parameter of the function listen is called backlog. It controls the number of incoming connections that are kept "waiting" if the program is already busy
print("Server B now listening at address => " + HOST + " :", PORT)


def verify_user(username, password):
	with open('login_credentials_B.csv', 'r') as credentials_file:
		credentials_file = csv.reader(credentials_file)
		for row in credentials_file:
			if(row[0] == username and row[1] == password):
				return True
		return False



# Function for handling conncections. This will be used to create threads
def clientthread(conn, addr):
	
	# Receiving from client
	data = conn.recv(1024).decode()
	data = data.split(' ')

	reply = str(int(verify_user(data[0], data[1])))

	conn.sendall(reply.encode())
	# came out of loop
	conn.close()
	print('Connection with ', addr[0] + ':' + str(addr[1]) + ' client terminated successfully.')


# Now keep talking with the client
while True:
    # wait to accept a connection - bloking call
    conn, addr = s.accept()
    print("Connection is successful with " + addr[0] + ":" + str(addr[1]))

    # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread, (conn, addr))

s.close()
