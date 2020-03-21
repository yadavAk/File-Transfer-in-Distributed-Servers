import socket
import sys, os
import csv
import time
from _thread import *
import tqdm

import buffer

HOST = "127.0.0.1"  # Symbolic name meaning all available interfaces
PORT = 8888 # int(input('Enter Arbitrary non-privileged port no. : '))

try :
	# create an AF_INET, STREAM socket (TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# SOCK_STREAM sockets is used for TCP sockets and SOCK_DGRAM is for UDP protocol(non-connection).
except socket.error as msg:
	print('Failed to create socket. Error code: ' + str(msg[0]) + ', Error message : ' + msg[1])
	sys.exit()

print('Socket Created Successfully !')


# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print("Bind failed. Error code : " + str(msg[0]) + " Message " + msg[1])
    sys.exit()

print("Socket bind complete")


s.listen(10)
# The parameter of the function listen is called backlog. It controls the number of incoming connections that are kept "waiting" if the program is already busy
print("Main Server now listening at address => " + HOST + " :", PORT)

def get_ip_port(name):
	rtl_file = open('localhost.rtl', 'r')
	lines = rtl_file.readlines()

	for line in lines:
		words = line.split('|')
		try:
			if(words[0].strip() == name):
				HOST = words[1].strip()
				PORT = int(words[2].strip())
		except ValueError:
			print('Something went wrong while parsing data from routing table file. Exiting...')
			sys.exit()
	return (HOST, PORT)


def verify_user(username, password):
	socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print('socket for distributed server 1 created')
	try:
		socket1.connect(get_ip_port('A'))
		socket2.connect(get_ip_port('B'))
		socket3.connect(get_ip_port('C'))
		socket4.connect(get_ip_port('D'))
	except socket.error as msg:
		print("Connection to dis. servers failed. Error code : " + str(msg[0]) + " Message " + msg[1])
		sys.exit()

	print("Socket connection to distributed servers complete")
	
	message = username + ' ' + password
	try :
		# Set the whole string
		socket1.sendall(message.encode())
		socket2.sendall(message.encode())
		socket3.sendall(message.encode())
		socket4.sendall(message.encode())
	except socket.error:
		# Send failed
		print('Sent to dis. server 1 failed')
		sys.exit()

	# Now receive data
	reply1 = int(socket1.recv(4096).decode())
	reply2 = int(socket2.recv(4096).decode())
	reply3 = int(socket3.recv(4096).decode())
	reply4 = float(socket4.recv(4096).decode())
	
	print('Reply of distributed servers ', reply1, reply2, reply3, reply4)
	socket1.close()
	socket2.close()
	socket3.close()
	socket4.close()

	return (reply1 + reply2*2 + reply3*3, reply4)



# Function for handling conncections. This will be used to create threads
def clientthread(conn, addr):
	# Sending message to connected client
	handshake_msg = '\nHello, ' + addr[0] + ':' + str(addr[1]) + '!\n'
	handshake_msg += 'Welcome to the server !!'
	conn.sendall(handshake_msg.encode())  # send only takes string

	while True:
		time.sleep(0.2)	# wait for above message to send successfully
		# Receiving from client
		msg1 = '\nPress \'q\' or \'EXIT\' or \'exit\' to close the connection\n'
		msg1 += 'Enter username : '
		conn.sendall(msg1.encode())

		username = conn.recv(1024).decode()

		temp = username.strip()
		# Sending to client
		if temp == 'q' or temp == 'EXIT' or temp == 'exit':
			reply = '\nOkay...closing the connection from server side\n'
			break
		else:
			reply = "\nOkay...username \'" + username + "\' received by main server successfully\n"
			print('Sending...', reply)
			conn.sendall(reply.encode())
			
			time.sleep(0.2)
			msg2 = 'Now, Enter the password : '
			conn.sendall(msg2.encode())

			# Receiving from client
			password = conn.recv(1024).decode()

			temp = password.strip()
			if temp == 'q' or temp == 'EXIT' or temp == 'exit':
				reply = '\nOkay...closing the connection from server side as requested by client\n'
				break

			(a, b) = verify_user(username, password)
			if a > 0:
				reply = '\nUsername and password are verified by server ' + str(a)
				
				if b != 101.0:
					reply += '\nAttendance of this user is ' + str(b) + '. '
					if(b >= 80.0):
						reply += 'Therefore, SPECIAL authentication is granted to this user !!'
					else:
						reply += 'Therefore, NO SPECIAL authentication to this user'
				conn.sendall(reply.encode())
				
				while True:
					# file receive
					meta_data = conn.recv(1024).decode().split()
					print(meta_data)
					buffer_size = int(meta_data[2])
					filename = 'received_file'
					filesize = int(meta_data[1])
					# start receiving the file from the socket
					# and writing to the file stream
					progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
					with open(filename, "wb") as f:
						while True:
							# read 1024 bytes from the socket (receive)
							bytes_read = conn.recv(buffer_size)
							# print('hi...', bytes_read)
							if not bytes_read:
								# nothing is received
								# file transmitting is done
								break
							# write to the file the bytes we just received
							f.write(bytes_read)
							# update the progress bar
							#time.sleep(0.001)
							progress.update(len(bytes_read))
					
					print('File transfer is successfull!!')
					yes_no_msg = conn.recv(1024).decode()
					if(yes_no_msg != 'y'):
						break
			else:
				reply = '\nOOPs...Either username or password is wrong, please try again !'
				conn.sendall(reply.encode())
		if True:
			pass

	conn.sendall(reply.encode())	
	conn.close()
	print('Connection with ', addr[0] + ':' + str(addr[1]) + ' client terminated successfully.')


# Now keep talking with the client
while True:
	try:
		# wait to accept a connection - blocking call
		conn, addr = s.accept()
		print("Connection is successful with " + addr[0] + ":" + str(addr[1]))

		# start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
		start_new_thread(clientthread, (conn, addr))
	except KeyboardInterrupt:
		print('KeyboardInterrupt: Exception caught. Exiting...')
		break

s.close()
