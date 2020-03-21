import socket	# for sockets
import sys, os	# for exit
import time
import select
import tqdm
import math

import buffer

host = 'localhost' #input('Enter hostname/ip : ') # e.g. 'localhost'
port = 8000 # int(input('Enter port no. of server 1 : ')) # e.g. 8000
port2 = 8800 # int(input('Enter port no. of server 2: ')) # e.g. 8000

try :
	# create an AF_INET, STREAM socket (TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

# Connect to remote server
try :
	s.connect((remote_ip, port))
	print('Client successfully connected to ' + host + ' on ip ' + remote_ip)
except :
	print('Failed to connect to server 1')

try :
	s2.connect((remote_ip, port2))
	print('Client successfully connected to ' + host + ' on ip ' + remote_ip)
except :
	print('Failed to connect to server 2')

#s.setblocking(0)
sbuf = buffer.Buffer(s)
sbuf2 = buffer.Buffer(s2)

def send_file_data(sbuf, data_bytes):
	sbuf.put_bytes(data_bytes)

	sbuf.set_timeout(2)
	temp = sbuf.get_utf8()
	sbuf.set_timeout(None)
	
	return temp

handshake_msg = sbuf.get_utf8()
handshake_msg2 = sbuf2.get_utf8()
print('From server 1 :', handshake_msg)
print('From server 2 :', handshake_msg2)

i = 0

while True:
	i = i+1
	msg1 = sbuf.get_utf8()
	msg2 = sbuf2.get_utf8()
	print(msg1)
	
	user_info = ''
	while user_info == '':
		user_info = input()
	
	try :
		# Set the whole string
		sbuf.put_utf8(user_info)
		sbuf2.put_utf8(user_info)
	except socket.error:
		# Send failed
		print('Sent failed from client')
		sys.exit()

	# Now receive data
	reply = sbuf.get_utf8()
	reply2 = sbuf2.get_utf8()
	print('From server 1 :', reply)
	print('From server 2 :', reply2)

	if(reply2[2] == 'O' and reply2[2] == 'O'):
		i = 0
	
	temp = user_info.strip()
	if temp == 'q' or temp == 'EXIT' or temp == 'exit':
		break

	if i > 1 :
		i = 0
		while True :
			filename = ''
			while filename == '' :
				filename =  input('Enter filename : ') # 'pg12169.txt'


			script_dir = os.path.dirname(__file__) # <-- absolute dir the script is in
			abs_file_path = os.path.join(script_dir, "client_files/" + filename)
			filesize = os.path.getsize('./client_files/' + filename)
			print('Filesize = ', filesize, 'Bytes')
			
			delay = input('Enter Delay between frames in ms : ')
			if(delay == ''):
				delay = '1'
				print('Taking default Delay :', delay, 'ms')

			BUFFER_SIZE = input('Enter frame size in bytes for file transfer : ')
			if BUFFER_SIZE == '':
				BUFFER_SIZE = '10240'
				print('Taking default Frame Size :', int(BUFFER_SIZE)/1024, 'KB')
			BUFFER_SIZE = int(BUFFER_SIZE)

			total_frames = math.ceil(filesize/BUFFER_SIZE)
			if total_frames % 2 == 0:
				filesize1 = int(total_frames/2)*BUFFER_SIZE
				filesize2 = filesize - filesize1
			else:
				filesize2 = int(total_frames/2)*BUFFER_SIZE
				filesize1 = filesize - filesize2
			
			if(filesize1 + filesize2 != filesize):
				print('Error in file size calculation')
			
			sbuf.put_utf8(f"{filename} {filesize1} {BUFFER_SIZE+1}")
			sbuf2.put_utf8(f"{filename} {filesize2} {BUFFER_SIZE+1}")
			
			# start sending the file

			progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
			with open(abs_file_path, "rb") as f:
				x = 0
				while True:
					# read the bytes from the file
					bytes_read = f.read(BUFFER_SIZE)
					# print('hello', bytes_read)
					if not bytes_read:
					# 	# file transmitting is done
						break
					temp = ''
					try :
						time.sleep(0.001*int(delay))
						if x%2 == 0:
							temp = send_file_data(sbuf, str(x).encode() + bytes_read)
						else :
							temp = send_file_data(sbuf2, str(x).encode() + bytes_read)
						
						if int(temp) != (x+1)%2:
							print('ACK received incorrectly')
							break

					except:
						print('Timeout reached, no ACK received')
					x = (x+1)%2
					# update the progress bar
					progress.update(len(bytes_read))
			#s.shutdown(socket.SHUT_WR)
			time.sleep(1)
			print(sbuf.get_utf8())
			print(sbuf2.get_utf8())
			yes_no_msg = ''
			while yes_no_msg == '':
				yes_no_msg = input('Send another file (y/n) : ')
			yes_no_msg = yes_no_msg.strip()

			sbuf.put_utf8(yes_no_msg)
			sbuf2.put_utf8(yes_no_msg)

			if(yes_no_msg != 'y'):
				print('Current user logging out...')
				break

s.close()
s2.close()
print('Client Sockets closed successfully. Exiting...')
