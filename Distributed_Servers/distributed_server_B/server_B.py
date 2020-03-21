import socket
import sys, time
import csv
from _thread import *
import tqdm

import buffer

rtl_file = open('../localhost.rtl', 'r')
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
	connbuf = buffer.Buffer(conn)

	# Receiving from client
	data = connbuf.get_utf8()
	data = data.split(' ')

	reply = str(int(verify_user(data[0], data[1])))

	connbuf.put_utf8(reply)

	while reply == '1':
		meta_data = connbuf.get_utf8()
		meta_data = meta_data.split()
		print(meta_data)

		filename = 'received_' + meta_data[0]
		filesize = int(meta_data[1])
		buffer_size = int(meta_data[2])

		# To rewrite file
		temp_f = open(filename, "wb")
		temp_f.close()

		# start receiving the file from the socket
		# and writing to the file stream
		progress = tqdm.tqdm(range(filesize), f"Receiving {meta_data[0]}", unit="B", unit_scale=True, unit_divisor=1024)
		remaining = filesize
		while remaining > 0:
			chunk_size = buffer_size if remaining >= buffer_size else remaining+1
			chunk = connbuf.get_bytes(chunk_size)
			if not chunk: break
			
			x = chunk[:1]
			#print('hello', remaining, chunk_size, chunk)
			# print('hello1', x)
			# print('hello2', chunk[1:])
			chunk = chunk[1:]
			f = open(filename, "ab")
			f.write(chunk)
			f.close()
			remaining -= len(chunk)
			
			x = int(x.decode())
			connbuf.put_utf8(str((x+1)%2))
			
			#time.sleep(0.01)
			progress.update(buffer_size-1)

		time.sleep(1)
		if remaining:
			final_msg = 'File incomplete.  Missing',remaining,'bytes.'
			print(final_msg)
		else:
			final_msg = 'From distributed server : File transmission done successfully.'
			print(final_msg)

		connbuf.put_utf8(final_msg)

		yes_no_msg = connbuf.get_utf8()
		if(yes_no_msg != 'y'):
			break


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
