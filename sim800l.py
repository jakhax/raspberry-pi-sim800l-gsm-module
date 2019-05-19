
import os,time,sys
import serial

def convert_to_string(buf):
    try:
        tt =  buf.decode('utf-8').strip()
        return tt
    except UnicodeError:
        tmp = bytearray(buf)
        for i in range(len(tmp)):
            if tmp[i]>127:
                tmp[i] = ord('#')
        return bytes(tmp).decode('utf-8').strip()

class SIM800L:
    def __init__(self,ser):
        try:
            self.ser=serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
        except Exception as e:
            sys.exit("Error: {}".format(e))
        self.incoming_action = None
        self.no_carrier_action = None
        self.clip_action = None
        self._clip = None
        self.msg_action = None
        self._msgid = 0
        self.savbuf = None

    def setup(self):
        self.command('ATE0\n')         # command echo off
        self.command('AT+CLIP=1\n')    # caller line identification
        self.command('AT+CMGF=1\n')    # plain text SMS
        self.command('AT+CLTS=1\n')    # enable get local timestamp mode
        self.command('AT+CSCLK=0\n')   # disable automatic sleep

    def callback_incoming(self,action):
        self.incoming_action = action

    def callback_no_carrier(self,action):
        self.no_carrier_action = action

    def get_clip(self):
        return self._clip
        
    def callback_msg(self,action):
        self.msg_action = action

    def get_msgid(self):
        return self._msgid

    def command(self, cmdstr, lines=1, waitfor=500, msgtext=None):
        while self.ser.in_waiting:
            self.ser.readline()
        self.ser.write(cmdstr.encode())
        if msgtext:
            self.ser.write(msgtext.encode())
        if waitfor>1000:
            time.sleep((waitfor-1000)/1000)
        buf=self.ser.readline() #discard linefeed etc
        #print(buf)
        buf=self.ser.readline()
        if not buf:
            return None
        result = convert_to_string(buf)
        if lines>1:
            self.savbuf = ''
            for i in range(lines-1):
                buf=self.ser.readline()
                if not buf:
                    return result
                buf = convert_to_string(buf)
                if not buf == '' and not buf == 'OK':
                    self.savbuf += buf+'\n'
        return result

    def send_sms(self,destno,msgtext):
        result = self.command('AT+CMGS="{}"\n'.format(destno),99,5000,msgtext+'\x1A')
        if result and result=='>' and self.savbuf:
            params = self.savbuf.split(':')
            if params[0]=='+CUSD' or params[0] == '+CMGS':
                return 'OK'
        return 'ERROR'

    def read_sms(self,id):
        result = self.command('AT+CMGR={}\n'.format(id),99)
        if result:
            params=result.split(',')
            if not params[0] == '':
                params2 = params[0].split(':')
                if params2[0]=='+CMGR':
                    number = params[1].replace('"',' ').strip()
                    date   = params[3].replace('"',' ').strip()
                    time   = params[4].replace('"',' ').strip()
                    return  [number,date,time,self.savbuf]
        return None

    def delete_sms(self,id):
        self.command('AT+CMGD={}\n'.format(id),1)

    def check_incoming(self): 
        if self.ser.in_waiting:
            buf=self.ser.readline()
            # print(buf)
            buf = convert_to_string(buf)
            params=buf.split(',')

            if params[0][0:5] == "+CMTI":
                self._msgid = int(params[1])
                if self.msg_action:
                    self.msg_action()

            elif params[0] == "NO CARRIER":
                    self.no_carrier_action()

            elif params[0] == "RING" or params[0][0:5] == "+CLIP":
                #@todo handle
                pass

    def read_and_delete_all(self):
        try:
            return self.read_sms(1)
        finally:
            self.command('AT+CMGDA="DEL ALL"\n',1)
