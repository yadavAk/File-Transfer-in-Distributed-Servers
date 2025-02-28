class Buffer:
    def __init__(self,s):
        '''Buffer a pre-created socket.
        '''
        self.sock = s
        self.buffer = b''

    def set_timeout(self,n):
        self.sock.settimeout(n)

    def get_bytes(self,n):
        '''Read exactly n bytes from the buffered socket.
           Return remaining buffer if <n bytes remain and socket closes.
        '''
        while len(self.buffer) < n:
            data = self.sock.recv(1024)
            if not data:
                data = self.buffer
                self.buffer = b''
                return data
            self.buffer += data
        # split off the message bytes from the buffer.
        data,self.buffer = self.buffer[:n],self.buffer[n:]
        return data

    def put_bytes(self,data):
        # we use sendall to assure transimission in 
        # busy networks
        self.sock.sendall(data)

    def get_utf8(self):
        '''Read a null-terminated UTF8 data string and decode it.
           Return an empty string if the socket closes before receiving a null.
        '''
        while b'\x00' not in self.buffer:
            data = self.sock.recv(1024)
            if not data:
                return ''
            self.buffer += data
        # split off the string from the buffer.
        data,_,self.buffer = self.buffer.partition(b'\x00')
        return data.decode()

    def put_utf8(self,s):
        if '\x00' in s:
            raise ValueError('string contains delimiter(null)')
        self.sock.sendall(s.encode() + b'\x00')