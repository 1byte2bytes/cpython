# Open an arbitrary URL
#
# See the following document for a tentative description of URLs:
#     Uniform Resource Locators              Tim Berners-Lee
#     INTERNET DRAFT                                    CERN
#     IETF URL Working Group                    14 July 1993
#     draft-ietf-uri-url-01.txt
#
# The object returned by URLopener().open(file) will differ per
# protocol.  All you know is that is has methods read(), readline(),
# readlines(), fileno(), close() and info().  The read*(), fileno()
# and close() methods work like those of open files. 
# The info() method returns an rfc822.Message object which can be
# used to query various info about the object, if available.
# (rfc822.Message objects are queried with the getheader() method.)

import socket
import regex


# This really consists of two pieces:
# (1) a class which handles opening of all sorts of URLs
#     (plus assorted utilities etc.)
# (2) a set of functions for parsing URLs
# XXX Should these be separated out into different modules?


# Shortcut for basic usage
_urlopener = None
def urlopen(url):
	global _urlopener
	if not _urlopener:
		_urlopener = URLopener()
	return _urlopener.open(url)
def urlretrieve(url):
	global _urlopener
	if not _urlopener:
		_urlopener = URLopener()
	return _urlopener.retrieve(url)
def urlcleanup():
	if _urlopener:
		_urlopener.cleanup()


# Class to open URLs.
# This is a class rather than just a subroutine because we may need
# more than one set of global protocol-specific options.
ftpcache = {}
class URLopener:

	# Constructor
	def __init__(self):
		self.addheaders = []
		self.tempcache = {}
		self.ftpcache = ftpcache
		# Undocumented feature: you can use a different
		# ftp cache by assigning to the .ftpcache member;
		# in case you want logically independent URL openers

	def __del__(self):
		self.close()

	def close(self):
		self.cleanup()

	def cleanup(self):
		import os
		for url in self.tempcache.keys():
			try:
				os.unlink(self.tempcache[url][0])
			except os.error:
				pass
			del self.tempcache[url]

	# Add a header to be used by the HTTP interface only
	# e.g. u.addheader('Accept', 'sound/basic')
	def addheader(self, *args):
		self.addheaders.append(args)

	# External interface
	# Use URLopener().open(file) instead of open(file, 'r')
	def open(self, url):
		type, url = splittype(unwrap(url))
 		if not type: type = 'file'
		name = 'open_' + type
		if '-' in name:
			import regsub
			name = regsub.gsub('-', '_', name)
		if not hasattr(self, name):
			raise IOError, ('url error', 'unknown url type', type)
		try:
			return getattr(self, name)(url)
		except socket.error, msg:
			raise IOError, ('socket error', msg)

	# External interface
	# retrieve(url) returns (filename, None) for a local object
	# or (tempfilename, headers) for a remote object
	def retrieve(self, url):
		if self.tempcache.has_key(url):
			return self.tempcache[url]
		url1 = unwrap(url)
		if self.tempcache.has_key(url1):
			self.tempcache[url] = self.tempcache[url1]
			return self.tempcache[url1]
		type, url1 = splittype(url1)
		if not type or type == 'file':
			try:
				fp = self.open_local_file(url1)
				del fp
				return splithost(url1)[1], None
			except IOError, msg:
				pass
		fp = self.open(url)
		headers = fp.info()
		import tempfile
		tfn = tempfile.mktemp()
		self.tempcache[url] = result = tfn, headers
		tfp = open(tfn, 'w')
		bs = 1024*8
		block = fp.read(bs)
		while block:
			tfp.write(block)
			block = fp.read(bs)
		del fp
		del tfp
		return result

	# Each method named open_<type> knows how to open that type of URL

	# Use HTTP protocol
	def open_http(self, url):
		import httplib
		host, selector = splithost(url)
		h = httplib.HTTP(host)
		h.putrequest('GET', selector)
		for args in self.addheaders: apply(h.putheader, args)
		errcode, errmsg, headers = h.getreply()
		if errcode == 200: return addinfo(h.getfile(), headers)
		else: raise IOError, ('http error', errcode, errmsg, headers)

	# Use Gopher protocol
	def open_gopher(self, url):
		import gopherlib
		host, selector = splithost(url)
		type, selector = splitgophertype(selector)
		selector, query = splitquery(selector)
		if query: fp = gopherlib.send_query(selector, query, host)
		else: fp = gopherlib.send_selector(selector, host)
		return addinfo(fp, noheaders())

	# Use local file or FTP depending on form of URL
	def open_file(self, url):
		try:
			return self.open_local_file(url)
		except IOError:
			return self.open_ftp(url)

	# Use local file
	def open_local_file(self, url):
		host, file = splithost(url)
		if not host: return addinfo(open(file, 'r'), noheaders())
		host, port = splitport(host)
		if not port and socket.gethostbyname(host) in (
			  localhost(), thishost()):
			return addinfo(open(file, 'r'), noheaders())
		raise IOError, ('local file error', 'not on local host')

	# Use FTP protocol
	def open_ftp(self, url):
		host, file = splithost(url)
		if not host: raise IOError, ('ftp error', 'no host given')
		host, port = splitport(host)
		host = socket.gethostbyname(host)
		if not port:
			import ftplib
			port = ftplib.FTP_PORT
		key = (host, port)
		try:
			if not self.ftpcache.has_key(key):
				self.ftpcache[key] = ftpwrapper(host, port)
			return addinfo(self.ftpcache[key].retrfile(file),
				  noheaders())
		except ftperrors(), msg:
			raise IOError, ('ftp error', msg)


# Utility functions

# Return the IP address of the magic hostname 'localhost'
_localhost = None
def localhost():
	global _localhost
	if not _localhost:
		_localhost = socket.gethostbyname('localhost')
	return _localhost

# Return the IP address of the current host
_thishost = None
def thishost():
	global _thishost
	if not _thishost:
		_thishost = socket.gethostbyname(socket.gethostname())
	return _thishost

# Return the set of errors raised by the FTP class
_ftperrors = None
def ftperrors():
	global _ftperrors
	if not _ftperrors:
		import ftplib
		_ftperrors = (ftplib.error_reply,
			      ftplib.error_temp,
			      ftplib.error_perm,
			      ftplib.error_proto)
	return _ftperrors

# Return an empty rfc822.Message object
_noheaders = None
def noheaders():
	global _noheaders
	if not _noheaders:
		import rfc822
		_noheaders = rfc822.Message(open('/dev/null', 'r'))
		_noheaders.fp.close()	# Recycle file descriptor
	return _noheaders


# Utility classes

# Class used by open_ftp() for cache of open FTP connections
class ftpwrapper:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.init()
	def init(self):
		import ftplib
		self.ftp = ftplib.FTP()
		self.ftp.connect(self.host, self.port)
		self.ftp.login()
	def retrfile(self, file):
		import ftplib
		try:
			self.ftp.voidcmd('TYPE I')
		except ftplib.all_errors:
			self.init()
			self.ftp.voidcmd('TYPE I')
		conn = None
		if file:
			try:
				cmd = 'RETR ' + file
				conn = self.ftp.transfercmd(cmd)
			except ftplib.error_perm, reason:
				if reason[:3] != '550':
					raise IOError, ('ftp error', reason)
		if not conn:
			# Try a directory listing
			if file: cmd = 'LIST ' + file
			else: cmd = 'LIST'
			conn = self.ftp.transfercmd(cmd)
		return addclosehook(conn.makefile('r'), self.ftp.voidresp)

# Base class for addinfo and addclosehook
class addbase:
	def __init__(self, fp):
		self.fp = fp
		self.read = self.fp.read
		self.readline = self.fp.readline
		self.readlines = self.fp.readlines
		self.fileno = self.fp.fileno
	def __repr__(self):
		return '<%s at %s whose fp = %s>' % (
			  self.__class__.__name__, `id(self)`, `self.fp`)
	def __del__(self):
		self.close()
	def close(self):
		self.read = None
		self.readline = None
		self.readlines = None
		self.fileno = None
		self.fp = None

# Class to add a close hook to an open file
class addclosehook(addbase):
	def __init__(self, fp, closehook, *hookargs):
		addbase.__init__(self, fp)
		self.closehook = closehook
		self.hookargs = hookargs
	def close(self):
		if self.closehook:
			apply(self.closehook, self.hookargs)
			self.closehook = None
			self.hookargs = None
		addbase.close(self)

# class to add an info() method to an open file
class addinfo(addbase):
	def __init__(self, fp, headers):
		addbase.__init__(self, fp)
		self.headers = headers
	def info(self):
		return self.headers


# Utility to combine a URL with a base URL to form a new URL

def basejoin(base, url):
	type, path = splittype(url)
	if type: return url
	host, path = splithost(path)
	basetype, basepath = splittype(base)
	basehost, basepath = splithost(basepath)
	basepath, basetag = splittag(basepath)
	basepath, basequery = splitquery(basepath)
	type = basetype or 'file'
	if path[:1] != '/':
		import string
		i = string.rfind(basepath, '/')
		if i < 0: basepath = '/'
		else: basepath = basepath[:i+1]
		path = basepath + path
	if not host: host = basehost
	if host: return type + '://' + host + path
	else: return type + ':' + path


# Utilities to parse URLs:
# unwrap('<URL:type//host/path>') --> 'type//host/path'
# splittype('type:opaquestring') --> 'type', 'opaquestring'
# splithost('//host[:port]/path') --> 'host[:port]', '/path'
# splitport('host:port') --> 'host', 'port'
# splitquery('/path?query') --> '/path', 'query'
# splittag('/path#tag') --> '/path', 'tag'
# splitgophertype('/Xselector') --> 'X', 'selector'

def unwrap(url):
	import string
	url = string.strip(url)
	if url[:1] == '<' and url[-1:] == '>':
		url = string.strip(url[1:-1])
	if url[:4] == 'URL:': url = string.strip(url[4:])
	return url

_typeprog = regex.compile('^\([^/:]+\):\(.*\)$')
def splittype(url):
	if _typeprog.match(url) >= 0: return _typeprog.group(1, 2)
	return None, url

_hostprog = regex.compile('^//\([^/]+\)\(.*\)$')
def splithost(url):
	if _hostprog.match(url) >= 0: return _hostprog.group(1, 2)
	return None, url

_portprog = regex.compile('^\(.*\):\([0-9]+\)$')
def splitport(host):
	if _portprog.match(host) >= 0: return _portprog.group(1, 2)
	return host, None

_queryprog = regex.compile('^\(.*\)\?\([^?]*\)$')
def splitquery(url):
	if _queryprog.match(url) >= 0: return _queryprog.group(1, 2)
	return url, None

_tagprog = regex.compile('^\(.*\)#\([^#]*\)$')
def splittag(url):
	if _tagprog.match(url) >= 0: return _tagprog.group(1, 2)
	return url, None

def splitgophertype(selector):
	if selector[:1] == '/' and selector[1:2]:
		return selector[1], selector[2:]
	return None, selector


# Test program
def test():
	import sys
	import regsub
	args = sys.argv[1:]
	if not args:
		args = [
			'/etc/passwd',
			'file:/etc/passwd',
			'file://localhost/etc/passwd',
			'ftp://ftp.cwi.nl/etc/passwd',
			'gopher://gopher.cwi.nl/11/',
			'http://www.cwi.nl/index.html',
			]
	try:
		for url in args:
			print '-'*10, url, '-'*10
			fn, h = urlretrieve(url)
			print fn, h
			if h:
				print '======'
				for k in h.keys(): print k + ':', h[k]
				print '======'
			fp = open(fn, 'r')
			data = fp.read()
			del fp
			print regsub.gsub('\r', '', data)
			fn, h = None, None
		print '-'*40
	finally:
		urlcleanup()

# Run test program when run as a script
if __name__ == '__main__':
	test()
