import socket
import sys, os, time, random
import csv
from _thread import *
import tqdm

import buffer

HOST = "127.0.0.1"  # Symbolic name meaning all available interfaces
PORT = int(input('Enter Arbitrary non-privileged port no. : '))

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
	HOST = ''
	PORT = 0
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


def handle_user(connbuf, username, password, server_number):

	dist_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print('Socket created for distributed server', server_number)
	
	try:
		dist_socket.connect(get_ip_port(chr(ord('A') + server_number-1)))
	except socket.error as msg:
		print("Connection to dist. servers failed. Error code : " + str(msg[0]) + " Message " + msg[1])
		sys.exit()

	print("Socket connection to distributed server", server_number, "complete")
	dist_socket_buf = buffer.Buffer(dist_socket)
	
	message = username + ' ' + password
	try :
		# Set the whole string
		dist_socket_buf.put_utf8(message)
	except socket.error:
		# Send failed
		print('Sent failed to distributed server', server_number)
		sys.exit()

	# Now receive data
	x = dist_socket_buf.get_utf8()
	# This condition handles attendance server case
	if(server_number == 4):
		node_reply = float(x)
		dist_socket.close()
		return node_reply
	else:
		node_reply = int(x)
		
	# Now node_reply contains the name/number of server which replied
	# if value of node_reply is 0, it means user verification is failed
	node_reply = node_reply*server_number

	if node_reply > 0:
		reply = '\nUsername and password are verified by server ' + str(node_reply)

		total_attendance = handle_user(connbuf, username, password, 4)

		print(reply, ' and attendance is', total_attendance)
		
		if total_attendance != 101.0:
			reply += '\nAttendance of this user is ' + str(total_attendance) + '. '
			if(total_attendance >= 80.0):
				reply += 'Therefore, SPECIAL authentication is granted to this user !!'
			else:
				reply += 'Therefore, NO SPECIAL authentication to this user'
		connbuf.put_utf8(reply)
		
		# file receive
		while True:
			meta_data = connbuf.get_utf8()
			dist_socket_buf.put_utf8(meta_data)
			meta_data = meta_data.split()
			print(meta_data)
			
			filesize = int(meta_data[1])
			buffer_size = int(meta_data[2])

			print('Random delay of 10 ms to 100 ms added to this server')

			# start receiving the file from the socket
			# and writing to the file stream
			remaining = filesize
			while remaining > 0:
				chunk_size = buffer_size if remaining >= buffer_size else remaining+2
				chunk = connbuf.get_bytes(chunk_size)
				if not chunk: break
				#print('hello', remaining, chunk_size, chunk)

				# Random delays of 10 ms to 100 ms in main server
				random_delay = random.randrange(10, 100)
				time.sleep(1/random_delay)
				dist_socket_buf.put_bytes(chunk)

				error_check = dist_socket_buf.get_utf8()
				connbuf.put_utf8(error_check)
				
				error_check_ = error_check.split()
				#print(error_check_)
				if(error_check_[1] == 'No_Error'):
					remaining -= len(chunk)-2

			if remaining:
				print('File incomplete.  Missing',remaining,'bytes.')
			else:
				print('File received and sent successfully.')
			
			connbuf.put_utf8(dist_socket_buf.get_utf8())
			
			yes_no_msg = connbuf.get_utf8()
			dist_socket_buf.put_utf8(yes_no_msg)
			if(yes_no_msg != 'y'):
				break

	dist_socket.close()
	return node_reply


# Function for handling conncections. This will be used to create threads
def clientthread(conn, addr):
	connbuf = buffer.Buffer(conn)
	# Sending message to connected client
	handshake_msg = '\nHello, ' + addr[0] + ':' + str(addr[1]) + '!\n'
	handshake_msg += 'Welcome to the server !!'
	connbuf.put_utf8(handshake_msg)  # send only takes string

	while True:
		time.sleep(0.2)	# wait for above message to send successfully
		# Receiving from client
		msg1 = '\nPress \'q\' or \'EXIT\' or \'exit\' to close the connection\n'
		msg1 += 'Enter username : '
		connbuf.put_utf8(msg1)

		username = connbuf.get_utf8()

		temp = username.strip()
		# Sending to client
		if temp == 'q' or temp == 'EXIT' or temp == 'exit':
			reply = '\nOkay...closing the connection from server side as requested by client\n'
			break
		else:
			reply = "\nOkay...username \'" + username + "\' received by main server successfully\n"
			print('Sending...', reply)
			connbuf.put_utf8(reply)
			
			time.sleep(0.2)
			msg2 = 'Now, Enter the password : '
			connbuf.put_utf8(msg2)

			# Receiving from client
			password = connbuf.get_utf8()

			temp = password.strip()
			if temp == 'q' or temp == 'EXIT' or temp == 'exit':
				reply = '\nOkay...closing the connection from server side as requested by client\n'
				break

			temp = 0
			for server_number in range(1, 4):
				print('Checking server', server_number, '...')
				temp += handle_user(connbuf, username, password, server_number)
				if temp > 0 :
					break
			if temp == 0 :
				reply = '\nOOPs...Either username or password is wrong, please try again !'
				connbuf.put_utf8(reply)


	connbuf.put_utf8(reply)	
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
