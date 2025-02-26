# This python script creates Finder aliases for all the
# dynamically-loaded modules that "live in" in a single
# shared library.
#
# This is sort-of a merger between Jack's MkPluginAliases
# and Guido's mkaliases.
#
# Jack Jansen, CWI, August 1996

import sys
import os
import macfs
import MacOS
verbose=0

SPLASH_LOCATE=512
SPLASH_REMOVE=513
SPLASH_CFM68K=514
SPLASH_PPC=515
SPLASH_NUMPY=516

ppc_goals = [
## 	("AE.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Ctl.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Dlg.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Evt.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Fm.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Help.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Icn.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Menu.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("List.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Qd.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Res.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Scrap.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Snd.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Sndihooks.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("TE.ppc.slb", "toolboxmodules.ppc.slb"),
## 	("Win.ppc.slb", "toolboxmodules.ppc.slb"),
## 
## 	("Cm.ppc.slb", "qtmodules.ppc.slb"),
## 	("Qt.ppc.slb", "qtmodules.ppc.slb"),

]

cfm68k_goals = [
## 	("AE.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Ctl.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Dlg.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Evt.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Fm.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Help.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Icn.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Menu.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("List.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Qd.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Res.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Scrap.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Snd.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Sndihooks.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("TE.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 	("Win.CFM68K.slb", "toolboxmodules.CFM68K.slb"),
## 
## 	("Cm.CFM68K.slb", "qtmodules.CFM68K.slb"),
## 	("Qt.CFM68K.slb", "qtmodules.CFM68K.slb"),
]

def gotopluginfolder():
	"""Go to the plugin folder, assuming we are somewhere in the Python tree"""
	import os
	
	while not os.path.isdir(":Mac:PlugIns"):
		os.chdir("::")
	os.chdir(":Mac:PlugIns")
	if verbose: print "current directory is", os.getcwd()
	
def loadtoolboxmodules():
	"""Attempt to load the Res module"""
	try:
		import Res
	except ImportError, arg:
		err1 = arg
		pass
	else:
		if verbose: print 'imported Res the standard way.'
		return
	
	# We cannot import it. First attempt to load the cfm68k version
	import imp
	try:
		dummy = imp.load_dynamic('Res', 'toolboxmodules.CFM68K.slb')
	except ImportError, arg:
		err2 = arg
		pass
	else:
		if verbose:  print 'Loaded Res from toolboxmodules.CFM68K.slb.'
		return
		
	# Ok, try the ppc version
	try:
		dummy = imp.load_dynamic('Res', 'toolboxmodules.ppc.slb')
	except ImportError, arg:
		err3 = arg
		pass
	else:
		if verbose:  print 'Loaded Res from toolboxmodules.ppc.slb.'
		return
	
	# Tough luck....
	print "I cannot import the Res module, nor load it from either of"
	print "toolboxmodules shared libraries. The errors encountered were:"
	print "import Res:", err1
	print "load from toolboxmodules.CFM68K.slb:", err2
	print "load from toolboxmodules.ppc.slb:", err3
	sys.exit(1)
	
def getextensiondirfile(fname):
	import macfs
	import MACFS
	vrefnum, dirid = macfs.FindFolder(MACFS.kOnSystemDisk, MACFS.kExtensionFolderType, 0)
	fss = macfs.FSSpec((vrefnum, dirid, fname))
	return fss.as_pathname()
	
def mkcorealias(src, altsrc):
	import string
	import macostools
	version = string.split(sys.version)[0]
	dst = getextensiondirfile(src+ ' ' + version)
	if not os.path.exists(os.path.join(sys.exec_prefix, src)):
		if not os.path.exists(os.path.join(sys.exec_prefix, altsrc)):
			if verbose:  print '*', src, 'not found'
			return 0
		src = altsrc
	try:
		os.unlink(dst)
	except os.error:
		pass
	macostools.mkalias(os.path.join(sys.exec_prefix, src), dst)
	if verbose:  print ' ', dst, '->', src
	return 1
	

def main():
	MacOS.splash(SPLASH_LOCATE)
	gotopluginfolder()
	
	loadtoolboxmodules()
	
	sys.path.append('::Mac:Lib')
	import macostools
		
	# Remove old .slb aliases and collect a list of .slb files
	didsplash = 0
	LibFiles = []
	allfiles = os.listdir(':')
	if verbose:  print 'Removing old aliases...'
	for f in allfiles:
		if f[-4:] == '.slb':
			finfo = macfs.FSSpec(f).GetFInfo()
			if finfo.Flags & 0x8000:
				if not didsplash:
					MacOS.splash(SPLASH_REMOVE)
					didsplash = 1
				if verbose:  print '  Removing', f
				os.unlink(f)
			else:
				LibFiles.append(f)
				if verbose:  print '  Found', f
	if verbose:  print
	
	# Create the new PPC aliases.
	didsplash = 0
	if verbose:  print 'Creating PPC aliases...'
	for dst, src in ppc_goals:
		if src in LibFiles:
			if not didsplash:
				MacOS.splash(SPLASH_PPC)
				didsplash = 1
			macostools.mkalias(src, dst)
			if verbose:  print ' ', dst, '->', src
		else:
			if verbose:  print '*', dst, 'not created:', src, 'not found'
	if verbose:  print
	
	# Create the CFM68K aliases.
	didsplash = 0
	if verbose:  print 'Creating CFM68K aliases...'
	for dst, src in cfm68k_goals:
		if src in LibFiles:
			if not didsplash:
				MacOS.splash(SPLASH_CFM68K)
				didsplash = 1
			macostools.mkalias(src, dst)
			if verbose:  print ' ', dst, '->', src
		else:
			if verbose:  print '*', dst, 'not created:', src, 'not found'
	if verbose:  print
			
	# Create the PythonCore alias(es)
	if verbose:  print 'Creating PythonCore aliases in Extensions folder...'
	os.chdir('::')
	n = 0
	n = n + mkcorealias('PythonCore', 'PythonCore')
	n = n + mkcorealias('PythonCorePPC', ':build.macppc.shared:PythonCorePPC')
	n = n + mkcorealias('PythonCoreCFM68K', ':build.mac68k.shared:PythonCoreCFM68K')
	
	if verbose and n == 0:
		sys.exit(1)
			
if __name__ == '__main__':
	if len(sys.argv) > 1 and sys.argv[1] == '-v':
		verbose = 1
	main()
