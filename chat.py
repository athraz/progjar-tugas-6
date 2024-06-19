import sys
import os
import json
import uuid
import logging
from queue import Queue


class Chat:
	def __init__(self):
		self.sessions={}
		self.users = {}
		self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
		self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
		self.users['lineker']={ 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
		self.groups = {}
  
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


if __name__=="__main__":
	j = Chat()