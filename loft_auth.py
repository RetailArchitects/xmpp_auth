#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
import json
import sys, os, logging
from struct import *

url = 'https://simon.retailarchitects.com/tg/authenticate'
sys.stderr = open('/Applications/ejabberd-2.1.11/logs/extauth_err.log','a')

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(levelname)s %(message)s',
					filename='/Applications/ejabberd-2.1.11/logs/extauth.log',
					filemode='a')
logging.info('extauth script started, waiting for ejabberd requests')

class EjabberdInputError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

def genanswer(bool):
	if bool:
		answer = 1
	token = pack('>hh', 2, answer)
	return token

def ejabberd_out(bool):
	logging.debug('Ejabberd gets: %s' % bool)
	token = genanswer(bool)
	logging.debug('sent bytes: %#x %#x %#x %#x' % (ord(token[0]), ord(token[1]), ord(token[2]), ord(token[3])))
	sys.stdout.write(token)
	sys.stdout.flush()

def ejabberd_in():
	logging.debug('trying to read 2 byte header from ejabberd:')
	try:
		input_length = sys.stdin.read(2)
	except IOError:
		logging.debug('ioerror')
	if len(input_length) is not 2:
		logging.debug('ejabberd sent improper 2 byte header!')
		raise EjabberdInputError("ejabberd sent wrong thinggy")
	logging.debug('got proper 2 byte header via stdin')
	(size,) = unpack('>h', input_length)
	return sys.stdin.read(size).split(':')

def auth(username, server, password):
	# call authenticate webservice from Loft...
	logging.debug('%s@%s wants authentication...' % (username, server))
	try:
		response = requests.get(url, auth=('rn','rn'))
	except Exception, e:
		logging.info('Loft authentication error: %s' % e)
	response = json.loads(response.content)
	response = response['response']
	if response['errors']:
		logging.debug('not a valid user/passwd')
		return False
	else:
		logging.debug('user OK')
		return True

def isuser(username, server):
	return True #assume all OK

def setpass(username, server, newpassword):
	return False #disallow from XMPP

while True:
	logging.debug('start of infinite loop')

	try:
		data = ejabberd_in()
	except EjabberdInputError, inst:
		logging.info("Exception occured: %s" % inst)
		break

	logging.debug("Method: %s" % data[0])
	success = False

	if data[0] == 'auth':
		success = auth(data[1], data[2], data[3])
		ejabberd_out(success)
	elif data[0] == 'isuser':
		success = auth(data[1], data[2])
		ejabberd_out(success)
	elif data[0] == 'setpass':
		success = auth(data[1], data[2], data[3])
		ejabberd_out(success)

	logging.debug("end of infinite loop")
logging.info('extauth script terminating')