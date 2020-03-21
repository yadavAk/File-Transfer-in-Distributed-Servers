import socket	# for sockets
import sys, os	# for exit
import time
import tqdm

import buffer

host = 'localhost' #input('Enter hostname/ip : ') # e.g. 'localhost'
port = 8888 # int(input('Enter port no. : ')) # e.g. 8000

try :
	# create an AF_INET, STREAM socket (TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# SOCK_STREAM sockets is used for TCP sockets and SOCK_DGRAM is for UDP protocol(non-connection).
except socket.error as msg:
	print('Failed to create socket. Error code: ' + str(msg[0]) + ', Error message : ' + msg[1])
	sys.exit()

print('Socket Created Successfully !')


try:
	remote_ip = socket.gethostbyname(host)
except socket.gaierror:
	# could not resolve
	print('Hostname could not be resolved. Exiting...')
	sys.exit()
	
print ('Ip address of ' + host + ' is ' + remote_ip)

BUFFER_SIZE = 1024 # int(input('Enter buffer size for file transfer : '))

# Connect to remote server
s.connect((remote_ip, port))

print('Client successfully connected to ' + host + ' on ip ' + remote_ip)

handshake_msg = s.recv(4096).decode()
print(handshake_msg)

i = 0

while True:
	i = i+1
	msg1 = s.recv(4096).decode()
	print(msg1)
	
	user_info = input()
	
	try :
		# Set the whole string
		s.sendall(user_info.encode())
	except socket.error:
		# Send failed
		print('Sent failed from client')
		sys.exit()

	# Now receive data
	reply = s.recv(4096).decode()
	print(reply)
	
	temp = user_info.strip()
	if temp == 'q' or temp == 'EXIT' or temp == 'exit':
		break

	if i > 1 :
		i = 0
		while True :
			filename = 'pg12169.txt' # input('Enter filename : ')
			filesize = os.path.getsize(filename)
			print('FILEsize - ', filesize, os.path)
			s.sendall(f"{filename} {filesize} {BUFFER_SIZE}".encode())
			# start sending the file
			
			progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
			with open(filename, "rb") as f:
				while True:
					# read the bytes from the file
					bytes_read = f.read(BUFFER_SIZE)
					if not bytes_read:
						# file transmitting is done
						break
					# we use sendall to assure transimission in 
					# busy networks
					time.sleep(0.005)
					s.sendall(bytes_read)
					# update the progress bar
					progress.update(len(bytes_read))
			s.shutdown(socket.SHUT_WR)
			time.sleep(1)
			yes_no_msg = input('Send another file (y/n) : ')
			yes_no_msg = yes_no_msg.strip()
			s.sendall(yes_no_msg.encode())
			if(yes_no_msg != 'y'):
				print('Current user logging out...')
				break

s.close()
print('Client Socket closed successfully. Exiting...')
