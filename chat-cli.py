import socket
import os
import json

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8889


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP,TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid=""

    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                   message="{} {}" . format(message,w)
                return self.sendmessage(usernameto,message)
            
            elif (command=='inbox'):
                return self.inbox()
            
            elif (command=='creategroup'):
                groupname = j[1].strip()
                grouppassword = j[2].strip()
                return self.creategroup(groupname, grouppassword)
            
            elif (command=='joingroup'):
                groupname = j[1].strip()
                grouppassword = j[2].strip()
                return self.joingroup(groupname, grouppassword)
            
            elif (command=='sendgroup'):
                groupname = j[1].strip()
                message=""
                for w in j[2:]:
                   message="{} {}" . format(message,w)
                return self.sendgroupmessage(groupname,message)
            
            elif (command=='inboxgroup'):
                groupname = j[1].strip()
                return self.inboxgroup(groupname)
            
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
                return "-Maaf, command tidak benar"

    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}

    def login(self,username,password):
        string="auth {} {} \r\n" . format(username,password)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def sendmessage(self,usernameto="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="send {} {} {} \r\n" . format(self.tokenid,usernameto,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])

    def inbox(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])

    def creategroup(self, groupname, grouppassword):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="creategroup {} {} {} \r\n" . format(self.tokenid, groupname, grouppassword)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "created group {}" . format(groupname)
        else:
            return "Error, {}" . format(result['message'])
        
    def joingroup(self, groupname, grouppassword):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="joingroup {} {} {} \r\n" . format(self.tokenid, groupname, grouppassword)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "joined group {}" . format(groupname)
        else:
            return "Error, {}" . format(result['message'])  
        
    def sendgroupmessage(self, groupname, message):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="sendgroup {} {} {} \r\n" . format(self.tokenid, groupname, message)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "group message sent to group {}" . format(groupname)
        else:
            return "Error, {}" . format(result['message'])
        
    def inboxgroup(self, groupname):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inboxgroup {} {} \r\n" . format(self.tokenid, groupname)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])
               
if __name__=="__main__":
    cc = ChatClient()
    while True:
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))
