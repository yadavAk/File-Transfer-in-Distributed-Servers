import socket	# for sockets
import sys, os, time, math, random
import select
import tqdm

import buffer

host = input('Enter hostname/ip : ') # e.g. 'localhost'
port = int(input('Enter port no. of server 1 : ')) # e.g. 8000
port2 = int(input('Enter port no. of server 2: ')) # e.g. 8000

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

	sbuf.set_timeout(5)
	temp = sbuf.get_utf8()
	sbuf.set_timeout(None)
	
	return temp

handshake_msg = sbuf.get_utf8()
handshake_msg2 = sbuf2.get_utf8()
print('From server 1 :', handshake_msg)
print('From server 2 :', handshake_msg2)

i = 0

while True:
	abort_transmission = 0
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
			delay = int(delay)

			BUFFER_SIZE = input('Enter frame size in bytes for file transfer : ')
			if BUFFER_SIZE == '':
				BUFFER_SIZE = '500'
				print('Taking default Frame Size :', int(BUFFER_SIZE)/1024, 'KB')
			BUFFER_SIZE = int(BUFFER_SIZE)

			error_probability = input('Enter error probability in transmission : ')
			if error_probability == '':
				error_probability = '0.1'
				print('Taking default error probability : ', error_probability)
			error_probability = int(float(error_probability)*100)

			total_frames = math.ceil(filesize/BUFFER_SIZE)
			if total_frames % 2 == 0:
				filesize1 = int(total_frames/2)*BUFFER_SIZE
				filesize2 = filesize - filesize1
			else:
				filesize2 = int(total_frames/2)*BUFFER_SIZE
				filesize1 = filesize - filesize2
			
			if(filesize1 + filesize2 != filesize):
				print('Error in file size calculation')
			
			sbuf.put_utf8(f"{filename} {filesize1} {BUFFER_SIZE+2}")
			sbuf2.put_utf8(f"{filename} {filesize2} {BUFFER_SIZE+2}")
			
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
					attempts = 0
					temp = [str(x), 'Error']
					while (int(temp[0]) == x or temp[1] == 'Error') and attempts < 5:
						if(attempts > 0):
							print('Retransmission attempt', attempts+1)
						else:
							attempts = 0
						try :
							time.sleep(0.001*delay)

							checksum = 0
							for byte in bytes_read:
								checksum = (checksum + byte)%256
								checksum = (checksum + 1)%256
							checksum_bytes = bytes([255-checksum])

							# Random error generation in frames
							random_no = random.randrange(0, 100)
							#print('Random number', random_no)
							#print('sending...0', bytes_read)
							send_bytes = bytes_read
							if random_no < error_probability:
								r_no = 1 #random.randrange(0, BUFFER_SIZE)
								send_bytes = bytes_read[0:r_no]+b'\x00'+bytes_read[r_no+1:]
								#print('\nr1\n', r_no, send_bytes)
								#send_bytes += bytes([(bytes_read[r_no])%256]) # Error byte
								#send_bytes += bytes_read[r_no+1:]
							#print('sending...1', send_bytes)
							# int.from_bytes(byt, byteorder=sys.byteorder)
							send_bytes = str(x).encode() + send_bytes
							send_bytes = send_bytes + checksum_bytes
							#print('sending...3', send_bytes)

							#print('HELLO', temp)
							if x%2 == 0:	
								temp = send_file_data(sbuf, send_bytes)
							else :
								temp = send_file_data(sbuf2, send_bytes)
							#print('HELLO', temp)
							temp = temp.split()
							if int(temp[0]) != (x+1)%2:
								print('ACK received incorrectly')
								attempts = attempts+1
							
							if temp[1] == 'Error':
								print('Error detected in this frame')
								attempts = attempts+1

						except:
							temp = [str(x), 'Error']
							attempts = attempts+1
							print('Timeout reached, no ACK received')
					if(attempts == 5):
						print('All attempts failed. Cannot transmitted data. Aborting transmission...')
						abort_transmission = 1
						break

					x = (x+1)%2
					# update the progress bar
					progress.update(len(bytes_read))
			#s.shutdown(socket.SHUT_WR)
			if abort_transmission == 1:
				break
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
	if abort_transmission == 1:
		break

s.close()
s2.close()
print('Client socket closed successfully. Exiting...')
