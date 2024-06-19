import sys
import os
import json
import uuid
import logging
import socket
import threading
from queue import Queue

class RealmThreadCommunication(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {
            'users': {},
            'groups': {}
        }
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.realm_dest_address, self.realm_dest_port))
            threading.Thread.__init__(self)
        except:
            return None

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    receivedmsg = "{}{}" . format(receivedmsg, data.decode())
                    if receivedmsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}
        
    def put_private(self, message):
        dest = message['msg_to']
        try:
            self.chat['users'][dest].put(message)
        except KeyError:
            self.chat['users'][dest] = Queue()
            self.chat['users'][dest].put(message)
    
    def put_group(self, message):
        dest = message['msg_to']
        try:
            self.chat['groups'][dest].put(message)
        except KeyError:
            self.chat['groups'][dest] = Queue()
            self.chat['groups'][dest].put(message)

class Chat:
	def __init__(self):
		self.sessions={}
		self.users = {}
		self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
		self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
		self.users['lineker']={ 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
		self.groups = {}
		self.realms = {}
		self.realms_info = {}
  
	def proses(self,data):
		j=data.split(" ")
		try:
			command=j[0].strip()
			# auth
			if (command == 'auth'):
				username=j[1].strip()
				password=j[2].strip()
				logging.warning("AUTH: auth {} {}" . format(username, password))
				return self.autentikasi_user(username, password)

			# send message between users
			elif (command == 'send'):
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				message=""
				for w in j[3:]:
					message="{} {}" . format(message,w)
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND: session {} send message from {} to {}" . format(sessionid, usernamefrom, usernameto))
				return self.send_message(sessionid, usernamefrom, usernameto, message)

			# get user inbox
			elif (command == 'inbox'):
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				logging.warning("INBOX: {}" . format(sessionid))
				return self.get_inbox(username)

			# create a group
			elif (command == 'creategroup'):
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				groupname = j[2].strip()
				grouppassword = j[3].strip()
				logging.warning("CREATE GROUP: session {} user {} created group {} with password {}" . format(sessionid, username, groupname, grouppassword))
				return self.create_group(sessionid, username, groupname, grouppassword)	

			# join a group
			elif (command == 'joingroup'):
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				groupname = j[2].strip()
				grouppassword = j[3].strip()
				logging.warning("JOIN GROUP: session {} user {} joined group {} with password {}" . format(sessionid, username, groupname, grouppassword))
				return self.join_group(sessionid, username, groupname, grouppassword)

			# send message to a group
			elif (command == 'sendgroup'):
				sessionid = j[1].strip()
				groupname = j[2].strip()
				message=""
				for w in j[3:]:
					message="{} {}" . format(message,w)
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND GROUP: session {} send message from {} to group {}" . format(sessionid, usernamefrom, groupname))
				return self.send_group_message(sessionid, usernamefrom, groupname, message)

			# get group inbox
			elif (command == 'inboxgroup'):
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				groupname = j[2].strip()
				logging.warning("INBOX: {}" . format(groupname))
				return self.get_group_inbox(sessionid, username, groupname)

			# create realm
			elif (command == 'createrealm'):
				realm_id = j[1].strip()
				realm_address = j[2].strip()
				realm_port = int(j[3].strip())
				src_address = j[4].strip()
				src_port = int(j[5].strip())
				logging.warning("CREATE REALM: {}:{} create realm {} to {}:{}" . format(src_address, src_port, realm_id, realm_address, realm_port))
				return self.create_realm(realm_id, realm_address, realm_port, src_address, src_port)

			# connect realm
			elif (command == 'ackrealm'):
				realm_id = j[1].strip()
				realm_address = j[2].strip()
				realm_port = int(j[3].strip())
				src_address = j[4].strip()
				src_port = int(j[5].strip())
				logging.warning("ACK REALM: {}:{} received realm {} connection request from {}:{}" . format(realm_id, realm_address, realm_port, src_address, src_port))
				return self.ack_realm(realm_id, src_address, src_port)

			# list all available realm
			elif (command == 'listrealm'):
				logging.warning("LIST REALM")
				return self.list_realm()

			# send private message through different realm
			elif (command == 'sendrealm'):
				src_address = j[1].strip()
				src_port = j[2].strip()
				sessionid = j[3].strip()
				realm_id = j[4].strip()
				usernameto = j[5].strip()
				message=""
				for w in j[3:]:
					message="{} {}" . format(message,w)
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND REALM: session {} send message from {} to {} through realm {}" . format(sessionid, usernamefrom, usernameto, realm_id))
				return self.send_realm(sessionid, src_address, src_port, realm_id, usernamefrom, usernameto, message)

			# get realm private message inbox
			elif (command == 'inboxrealm'):
				sessionid = j[1].strip()
				realm_id = j[2].strip()
				username = self.sessions[sessionid]['username']
				logging.warning("INBOX REALM: session {} username {} realm {}" . format(sessionid, username, realm_id))
				return self.get_realm_inbox(sessionid, username, realm_id)

			elif (command == 'rcvinboxrealm'):
				username = j[1].strip()
				realm_id = j[2].strip()
				logging.warning("RECEIVE INBOX REALM: username {} realm {}" . format(username, realm_id))
				return self.rcv_realm_inbox(username, realm_id)

			# send group message through different realm
			elif (command == 'sendgrouprealm'):
				src_address = j[1].strip()
				src_port = j[2].strip()
				sessionid = j[3].strip()
				realm_id = j[4].strip()
				groupname = j[5].strip()
				message=""
				for w in j[3:]:
					message="{} {}" . format(message,w)
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND GROUP REALM: session {} send message from {} to group {} through realm {}" . format(sessionid, usernamefrom, groupname, realm_id))
				return self.send_group_realm(sessionid, src_address, src_port, realm_id, usernamefrom, groupname, message)	

			# get realm group message inbox
			elif (command == 'inboxgrouprealm'):
				sessionid = j[1].strip()
				realm_id = j[2].strip()
				groupname = j[3].strip()
				username = self.sessions[sessionid]['username']
				logging.warning("INBOX GROUP REALM: session {} username {} groupname {} realm {}" . format(sessionid, username, groupname, realm_id))
				return self.get_realm_group_inbox(sessionid, username, groupname, realm_id)

			elif (command == 'rcvinboxgrouprealm'):
				groupname = j[1].strip()
				realm_id = j[2].strip()
				logging.warning("RECEIVE INBOX GROUP REALM: groupname {} realm {}" . format(groupname, realm_id))
				return self.rcv_realm_group_inbox(groupname, realm_id)			

			else:
				return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
		except KeyError:
			return { 'status': 'ERROR', 'message' : 'Informasi tidak ditemukan'}
		except IndexError:
			return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}

	def autentikasi_user(self,username,password):
		if (username not in self.users):
			return { 'status': 'ERROR', 'message': 'User Tidak Ada' }
		if (self.users[username]['password']!= password):
			return { 'status': 'ERROR', 'message': 'Password Salah' }
		tokenid = str(uuid.uuid4()) 
		self.sessions[tokenid]={ 'username': username, 'userdetail':self.users[username]}
		return { 'status': 'OK', 'tokenid': tokenid }

	def get_user(self,username):
		if (username not in self.users):
			return False
		return self.users[username]

	def send_message(self,sessionid,username_from,username_dest,message):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		
		if (s_fr==False or s_to==False):
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

		message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
		outqueue_sender = s_fr['outgoing']
		inqueue_receiver = s_to['incoming']
		try:	
			outqueue_sender[username_from].put(message)
		except KeyError:
			outqueue_sender[username_from]=Queue()
			outqueue_sender[username_from].put(message)
		try:
			inqueue_receiver[username_from].put(message)
		except KeyError:
			inqueue_receiver[username_from]=Queue()
			inqueue_receiver[username_from].put(message)
		return {'status': 'OK', 'message': 'Message Sent'}

	def get_inbox(self,username):
		s_fr = self.get_user(username)
		incoming = s_fr['incoming']
		msgs={}
		for users in incoming:
			msgs[users]=[]
			while not incoming[users].empty():
				msgs[users].append(s_fr['incoming'][users].get_nowait())
			
		return {'status': 'OK', 'messages': msgs}

	def get_group(self, groupname):
		if (groupname not in self.groups):
			return False
		return self.groups[groupname]

	def create_group(self, sessionid, username, groupname, grouppassword):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (groupname in self.groups):
			return {'status': 'ERROR', 'message': 'Group Sudah Ada'}
		self.groups[groupname] = {
			'nama': groupname,
			'password': grouppassword,
			'members': [],
			'incoming': {}
		}
		self.groups[groupname]['members'].append(username)
		return {'status': 'OK', 'message': 'Berhasil Membuat Group'}

	def join_group(self, sessionid, username, groupname, grouppassword):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (groupname not in self.groups):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if (username in self.groups[groupname]['members']):
			return {'status': 'ERROR', 'message': 'User Sudah Join Group'}
		if (self.groups[groupname]['password'] != grouppassword):
			return {'status': 'ERROR', 'message': 'Password Group Salah'}
		self.groups[groupname]['members'].append(username)
		return {'status': 'OK', 'message': 'Berhasil Join Group'}
     
	def send_group_message(self, sessionid, username_from, groupname, message):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (groupname not in self.groups):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if (username_from not in self.groups[groupname]['members']):
			return {'status': 'ERROR', 'message': 'User Bukan Member Group'}
		s_fr = self.get_user(username_from)
		g_to = self.get_group(groupname)

		if (s_fr==False):
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		if (g_to==False):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}

		message = { 'msg_from': s_fr['nama'], 'msg_to': g_to['nama'], 'msg': message }
		outqueue_sender = s_fr['outgoing']
		inqueue_receiver = g_to['incoming']
		try:	
			outqueue_sender[username_from].put(message)
		except KeyError:
			outqueue_sender[username_from]=Queue()
			outqueue_sender[username_from].put(message)
		try:
			inqueue_receiver[username_from].put(message)
		except KeyError:
			inqueue_receiver[username_from]=Queue()
			inqueue_receiver[username_from].put(message)
		return {'status': 'OK', 'message': 'Message Sent To Group'}

	def get_group_inbox(self, sessionid, username, groupname):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (groupname not in self.groups):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if (username not in self.groups[groupname]['members']):
			return {'status': 'ERROR', 'message': 'User Bukan Member Group'}

		g_fr = self.get_group(groupname)
		incoming = g_fr['incoming']
		msgs={}
		for users in incoming:
			msgs[users]=[]
			temp_queue = incoming[users].queue.copy()
			while len(temp_queue) > 0:
				msgs[users].append(temp_queue.pop())
			
		return {'status': 'OK', 'messages': msgs}

	def create_realm(self, realm_id, realm_address, realm_port, src_address, src_port):
		if (realm_id in self.realms_info):
			return { 'status': 'ERROR', 'message': 'Realm sudah ada' }
            
		self.realms[realm_id] = RealmThreadCommunication(self, realm_address, realm_port)
		result = self.realms[realm_id].sendstring("ackrealm {} {} {} {} {}\r\n" . format(realm_id, realm_address, realm_port, src_address, src_port))
		if result['status']=='OK':
			self.realms_info[realm_id] = {'serverip': realm_address, 'port': realm_port}
			return result
		else:
			return {'status': 'ERROR', 'message': 'Realm unreachable'}

	def ack_realm(self, realm_id, src_address, src_port):
		self.realms[realm_id] = RealmThreadCommunication(self, src_address, src_port)
		self.realms_info[realm_id] = {'serverip': src_address, 'port': src_port}
		return {'status': 'OK', 'message': 'Connect realm berhasil'}

	def list_realm(self):
		return {'status': 'OK', 'message': self.realms_info}

	def send_realm(self, sessionid, src_address, src_port, realm_id, usernamefrom, usernameto, message):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (realm_id not in self.realms_info):
			return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}

		s_fr = self.get_user(usernamefrom)
		s_to = self.get_user(usernameto)
		
		if (s_fr==False or s_to==False):
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

		msg_from = f"{s_fr['nama']} ({src_address}:{src_port})"
		message = {'msg_from': msg_from, 'msg_to': s_to['nama'], 'msg': message}
		self.realms[realm_id].put_private(message)
		return {'status': 'OK', 'message': 'Realm Private Message Sent'}

	def get_realm_inbox(self, sessionid, username, realm_id):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (realm_id not in self.realms_info):
			return { 'status': 'ERROR', 'message': 'Realm Tidak Ditemukan' }
		return self.realms[realm_id].sendstring("rcvinboxrealm {} {}\r\n".format(username, realm_id))

	def rcv_realm_inbox(self, username, realm_id):
		if (realm_id not in self.realms_info):
			return { 'status': 'ERROR', 'message': 'Realm Tidak Ditemukan' }
		s_fr = self.get_user(username)
		msgs = []
		q = self.realms[realm_id].chat['users'][s_fr['nama']].queue.copy()
		while len(q) > 0:
			msgs.append(q.pop())
		return {'status': 'OK', 'messages': msgs}

	def send_group_realm(self, sessionid, src_address, src_port, realm_id, usernamefrom, groupname, message):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (realm_id not in self.realms_info):
			return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
		if (usernamefrom not in self.groups[groupname]['members']):
			return {'status': 'ERROR', 'message': 'User Bukan Member Group'}

		s_fr = self.get_user(usernamefrom)
		g_to = self.get_group(groupname)
		
		if (s_fr==False):
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		if (g_to==False):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}

		msg_from = f"{s_fr['nama']} ({src_address}:{src_port})"
		message = {'msg_from': msg_from, 'msg_to': g_to['nama'], 'msg': message}
		self.realms[realm_id].put_group(message)
		return {'status': 'OK', 'message': 'Realm Group Message Sent'}

	def get_realm_group_inbox(self, sessionid, username, groupname, realm_id):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if (groupname not in self.groups):
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if (username not in self.groups[groupname]['members']):
			return {'status': 'ERROR', 'message': 'User Bukan Member Group'}
		if (realm_id not in self.realms_info):
			return { 'status': 'ERROR', 'message': 'Realm Tidak Ditemukan' }
		return self.realms[realm_id].sendstring("rcvinboxgrouprealm {} {}\r\n".format(groupname, realm_id))

	def rcv_realm_group_inbox(self, groupname, realm_id):
		if (realm_id not in self.realms_info):
			return { 'status': 'ERROR', 'message': 'Realm Tidak Ditemukan' }
		g_fr = self.get_group(groupname)
		msgs = []
		q = self.realms[realm_id].chat['groups'][g_fr['nama']].queue.copy()
		while len(q) > 0:
			msgs.append(q.pop())
		return {'status': 'OK', 'messages': msgs}
     
if __name__=="__main__":
	j = Chat()