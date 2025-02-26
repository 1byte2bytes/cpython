# A minimal text editor.
#
# To be done:
# - Functionality: find, etc.

from Menu import DrawMenuBar
from FrameWork import *
import Win
import Qd
import Res
import Fm
import waste
import WASTEconst
import Scrap
import os
import macfs

UNDOLABELS = [ # Indexed by WEGetUndoInfo() value
	None, "", "typing", "Cut", "Paste", "Clear", "Drag", "Style"]
	
# Style and size menu. Note that style order is important (tied to bit values)
STYLES = [
	("Bold", "B"), ("Italic", "I"), ("Underline", "U"), ("Outline", "O"),
	("Shadow", ""), ("Condensed", ""), ("Extended", "")
	]
SIZES = [ 9, 10, 12, 14, 18, 24]
	
BIGREGION=Qd.NewRgn()
Qd.SetRectRgn(BIGREGION, -16000, -16000, 16000, 16000)

class WasteWindow(ScrolledWindow):
	def open(self, path, name, data):
		self.path = path
		self.name = name
		r = windowbounds(400, 400)
		w = Win.NewWindow(r, name, 1, 0, -1, 1, 0x55555555)
		self.wid = w
		vr = 0, 0, r[2]-r[0]-15, r[3]-r[1]-15
		dr = (0, 0, 10240, 0)
		Qd.SetPort(w)
		Qd.TextFont(4)
		Qd.TextSize(9)
		flags = WASTEconst.weDoAutoScroll | WASTEconst.weDoOutlineHilite | \
				WASTEconst.weDoUndo
		self.ted = waste.WENew(dr, vr, flags)
		self.ted.WEInstallTabHooks()
		style, soup = self.getstylesoup()
		self.ted.WEInsert(data, style, soup)
		self.ted.WESetSelection(0,0)
		self.ted.WECalText()
		self.ted.WEResetModCount()
		w.DrawGrowIcon()
		self.scrollbars()
		self.do_postopen()
		self.do_activate(1, None)
		
	def getstylesoup(self):
		if not self.path:
			return None, None
		oldrf = Res.CurResFile()
		try:
			rf = Res.OpenResFile(self.path)
		except Res.Error:
			return None, None
		try:
			hstyle = Res.Get1Resource('styl', 128)
			hstyle.DetachResource()
		except Res.Error:
			hstyle = None
		try:
			hsoup = Res.Get1Resource('SOUP', 128)
			hsoup.DetachResource()
		except Res.Error:
			hsoup = None
		Res.CloseResFile(rf)
		Res.UseResFile(oldrf)
		return hstyle, hsoup
				
	def do_idle(self, event):
		(what, message, when, where, modifiers) = event
		Qd.SetPort(self.wid)
		self.ted.WEIdle()	
		if self.ted.WEAdjustCursor(where, BIGREGION):
			return
		Qd.SetCursor(Qd.qd.arrow)
		
	def getscrollbarvalues(self):
		dr = self.ted.WEGetDestRect()
		vr = self.ted.WEGetViewRect()
		vx = self.scalebarvalue(dr[0], dr[2], vr[0], vr[2])
		vy = self.scalebarvalue(dr[1], dr[3], vr[1], vr[3])
		return vx, vy
		
	def scrollbar_callback(self, which, what, value):
		if which == 'y':
			if what == 'set':
				height = self.ted.WEGetHeight(0, 0x3fffffff)
				cur = self.getscrollbarvalues()[1]
				delta = (cur-value)*height/32767
			if what == '-':
				topline_off,dummy = self.ted.WEGetOffset((1,1))
				topline_num = self.ted.WEOffsetToLine(topline_off)
				delta = self.ted.WEGetHeight(topline_num, topline_num+1)
			elif what == '--':
				delta = (self.ted.WEGetViewRect()[3]-10)
				if delta <= 0:
					delta = 10 # Random value
			elif what == '+':
				# XXXX Wrong: should be bottom line size
				topline_off,dummy = self.ted.WEGetOffset((1,1))
				topline_num = self.ted.WEOffsetToLine(topline_off)
				delta = -self.ted.WEGetHeight(topline_num, topline_num+1)
			elif what == '++':
				delta = -(self.ted.WEGetViewRect()[3]-10)
				if delta >= 0:
					delta = -10
			self.ted.WEScroll(0, delta)
		else:
			if what == 'set':
				return # XXXX
			vr = self.ted.WEGetViewRect()
			winwidth = vr[2]-vr[0]
			if what == '-':
				delta = winwidth/10
			elif what == '--':
				delta = winwidth/2
			elif what == '+':
				delta = -winwidth/10
			elif what == '++':
				delta = -winwidth/2
			self.ted.WEScroll(delta, 0)
		# Pin the scroll
		l, t, r, b = self.ted.WEGetDestRect()
		vl, vt, vr, vb = self.ted.WEGetViewRect()
		if t > 0 or l > 0:
			dx = dy = 0
			if t > 0: dy = -t
			if l > 0: dx = -l
			self.ted.WEScroll(dx, dy)
		elif b < vb:
			self.ted.WEScroll(0, b-vb)

		
	def do_activate(self, onoff, evt):
		Qd.SetPort(self.wid)
		ScrolledWindow.do_activate(self, onoff, evt)
		if onoff:
			self.ted.WEActivate()
			self.parent.active = self
			self.parent.updatemenubar()
		else:
			self.ted.WEDeactivate()

	def do_update(self, wid, event):
		region = wid.GetWindowPort().visRgn
		if Qd.EmptyRgn(region):
			return
		Qd.EraseRgn(region)
		self.ted.WEUpdate(region)
		self.updatescrollbars()
		
	def do_postresize(self, width, height, window):
		l, t, r, b = self.ted.WEGetViewRect()
		vr = (l, t, l+width-15, t+height-15)
		self.ted.WESetViewRect(vr)
		Win.InvalRect(vr)
		ScrolledWindow.do_postresize(self, width, height, window)
		
	def do_contentclick(self, local, modifiers, evt):
		(what, message, when, where, modifiers) = evt
		self.ted.WEClick(local, modifiers, when)
		self.updatescrollbars()
		self.parent.updatemenubar()

	def do_char(self, ch, event):
		self.ted.WESelView()
		(what, message, when, where, modifiers) = event
		self.ted.WEKey(ord(ch), modifiers)
		self.updatescrollbars()
		self.parent.updatemenubar()
		
	def close(self):
		if self.ted.WEGetModCount():
			save = EasyDialogs.AskYesNoCancel('Save window "%s" before closing?'%self.name, 1)
			if save > 0:
				self.menu_save()
			elif save < 0:
				return
		if self.parent.active == self:
			self.parent.active = None
		self.parent.updatemenubar()
		del self.ted
		self.do_postclose()
		
	def menu_save(self):
		if not self.path:
			self.menu_save_as()
			return # Will call us recursively
		#
		# First save data
		#
		dhandle = self.ted.WEGetText()
		data = dhandle.data
		fp = open(self.path, 'wb')  # NOTE: wb, because data has CR for end-of-line
		fp.write(data)
		if data[-1] <> '\r': fp.write('\r')
		fp.close()
		#
		# Now save style and soup
		#
		oldresfile = Res.CurResFile()
		try:
			rf = Res.OpenResFile(self.path)
		except Res.Error:
			Res.CreateResFile(self.path)
			rf = Res.OpenResFile(self.path)
		styles = Res.Resource('')
		soup = Res.Resource('')
		self.ted.WECopyRange(0, 0x3fffffff, None, styles, soup)
		styles.AddResource('styl', 128, '')
		soup.AddResource('SOUP', 128, '')
		Res.CloseResFile(rf)
		Res.UseResFile(oldresfile)
		
		self.ted.WEResetModCount()
		
	def menu_save_as(self):
		fss, ok = macfs.StandardPutFile('Save as:')
		if not ok: return
		self.path = fss.as_pathname()
		self.name = os.path.split(self.path)[-1]
		self.wid.SetWTitle(self.name)
		self.menu_save()
		
	def menu_cut(self):
		self.ted.WESelView()
		self.ted.WECut()
		Scrap.ZeroScrap()
		self.ted.WECut()
		self.updatescrollbars()
		self.parent.updatemenubar()
		
	def menu_copy(self):
		Scrap.ZeroScrap()
		self.ted.WECopy()
		self.updatescrollbars()
		self.parent.updatemenubar()
		
	def menu_paste(self):
		self.ted.WESelView()
		self.ted.WEPaste()
		self.updatescrollbars()
		self.parent.updatemenubar()
		
	def menu_clear(self):
		self.ted.WESelView()
		self.ted.WEDelete()
		self.updatescrollbars()
		self.parent.updatemenubar()

	def menu_undo(self):
		self.ted.WEUndo()
		self.updatescrollbars()
		self.parent.updatemenubar()
		
	def menu_setfont(self, font):
		font = Fm.GetFNum(font)
		self.mysetstyle(WASTEconst.weDoFont, (font, 0, 0, (0,0,0)))
		self.parent.updatemenubar()
				
	def menu_modface(self, face):
		self.mysetstyle(WASTEconst.weDoFace|WASTEconst.weDoToggleFace, 
			(0, face, 0, (0,0,0)))

	def menu_setface(self, face):
		self.mysetstyle(WASTEconst.weDoFace|WASTEconst.weDoReplaceFace, 
			(0, face, 0, (0,0,0)))

	def menu_setsize(self, size):
		self.mysetstyle(WASTEconst.weDoSize, (0, 0, size, (0,0,0)))
								
	def menu_incsize(self, size):
		self.mysetstyle(WASTEconst.weDoAddSize, (0, 0, size, (0,0,0)))

	def mysetstyle(self, which, how):
		self.ted.WESelView()
		self.ted.WESetStyle(which, how)
		self.parent.updatemenubar()
								
	def have_selection(self):
		start, stop = self.ted.WEGetSelection()
		return start < stop
		
	def can_paste(self):
		return self.ted.WECanPaste()
		
	def can_undo(self):
		which, redo = self.ted.WEGetUndoInfo()
		which = UNDOLABELS[which]
		if which == None: return None
		if redo:
			return "Redo "+which
		else:
			return "Undo "+which
			
	def getruninfo(self):
		all = (WASTEconst.weDoFont | WASTEconst.weDoFace | WASTEconst.weDoSize)
		dummy, mode, (font, face, size, color) = self.ted.WEContinuousStyle(all)
		if not (mode & WASTEconst.weDoFont):
			font = None
		else:
			font = Fm.GetFontName(font)
		if not (mode & WASTEconst.weDoFace): fact = None
		if not (mode & WASTEconst.weDoSize): size = None
		return font, face, size

class Wed(Application):
	def __init__(self):
		Application.__init__(self)
		self.num = 0
		self.active = None
		self.updatemenubar()
		waste.STDObjectHandlers()
		
	def makeusermenus(self):
		self.filemenu = m = Menu(self.menubar, "File")
		self.newitem = MenuItem(m, "New window", "N", self.open)
		self.openitem = MenuItem(m, "Open...", "O", self.openfile)
		self.closeitem = MenuItem(m, "Close", "W", self.closewin)
		m.addseparator()
		self.saveitem = MenuItem(m, "Save", "S", self.save)
		self.saveasitem = MenuItem(m, "Save as...", "", self.saveas)
		m.addseparator()
		self.quititem = MenuItem(m, "Quit", "Q", self.quit)
		
		self.editmenu = m = Menu(self.menubar, "Edit")
		self.undoitem = MenuItem(m, "Undo", "Z", self.undo)
		self.cutitem = MenuItem(m, "Cut", "X", self.cut)
		self.copyitem = MenuItem(m, "Copy", "C", self.copy)
		self.pasteitem = MenuItem(m, "Paste", "V", self.paste)
		self.clearitem = MenuItem(m, "Clear", "", self.clear)
		
		self.makefontmenu()
		
		# Groups of items enabled together:
		self.windowgroup = [self.closeitem, self.saveitem, self.saveasitem,
			self.editmenu, self.fontmenu, self.facemenu, self.sizemenu]
		self.focusgroup = [self.cutitem, self.copyitem, self.clearitem]
		self.windowgroup_on = -1
		self.focusgroup_on = -1
		self.pastegroup_on = -1
		self.undo_label = "never"
		self.ffs_values = ()
		
	def makefontmenu(self):
		self.fontmenu = Menu(self.menubar, "Font")
		self.fontnames = getfontnames()
		self.fontitems = []
		for n in self.fontnames:
			m = MenuItem(self.fontmenu, n, "", self.selfont)
			self.fontitems.append(m)
		self.facemenu = Menu(self.menubar, "Style")
		self.faceitems = []
		for n, shortcut in STYLES:
			m = MenuItem(self.facemenu, n, shortcut, self.selface)
			self.faceitems.append(m)
		self.facemenu.addseparator()
		self.faceitem_normal = MenuItem(self.facemenu, "Normal", "N", 
			self.selfacenormal)
		self.sizemenu = Menu(self.menubar, "Size")
		self.sizeitems = []
		for n in SIZES:
			m = MenuItem(self.sizemenu, `n`, "", self.selsize)
			self.sizeitems.append(m)
		self.sizemenu.addseparator()
		self.sizeitem_bigger = MenuItem(self.sizemenu, "Bigger", "+", 
			self.selsizebigger)
		self.sizeitem_smaller = MenuItem(self.sizemenu, "Smaller", "-", 
			self.selsizesmaller)
					
	def selfont(self, id, item, *rest):
		if self.active:
			font = self.fontnames[item-1]
			self.active.menu_setfont(font)
		else:
			EasyDialogs.Message("No active window?")

	def selface(self, id, item, *rest):
		if self.active:
			face = (1<<(item-1))
			self.active.menu_modface(face)
		else:
			EasyDialogs.Message("No active window?")

	def selfacenormal(self, *rest):
		if self.active:
			self.active.menu_setface(0)
		else:
			EasyDialogs.Message("No active window?")

	def selsize(self, id, item, *rest):
		if self.active:
			size = SIZES[item-1]
			self.active.menu_setsize(size)
		else:
			EasyDialogs.Message("No active window?")

	def selsizebigger(self, *rest):
		if self.active:
			self.active.menu_incsize(2)
		else:
			EasyDialogs.Message("No active window?")

	def selsizesmaller(self, *rest):
		if self.active:
			self.active.menu_incsize(-2)
		else:
			EasyDialogs.Message("No active window?")

	def updatemenubar(self):
		changed = 0
		on = (self.active <> None)
		if on <> self.windowgroup_on:
			for m in self.windowgroup:
				m.enable(on)
			self.windowgroup_on = on
			changed = 1
		if on:
			# only if we have an edit menu
			on = self.active.have_selection()
			if on <> self.focusgroup_on:
				for m in self.focusgroup:
					m.enable(on)
				self.focusgroup_on = on
				changed = 1
			on = self.active.can_paste()
			if on <> self.pastegroup_on:
				self.pasteitem.enable(on)
				self.pastegroup_on = on
				changed = 1
			on = self.active.can_undo()
			if on <> self.undo_label:
				if on:
					self.undoitem.enable(1)
					self.undoitem.settext(on)
					self.undo_label = on
				else:
					self.undoitem.settext("Nothing to undo")
					self.undoitem.enable(0)
				changed = 1
			if self.updatefontmenus():
				changed = 1
		if changed:
			DrawMenuBar()
			
	def updatefontmenus(self):
		info = self.active.getruninfo()
		if info == self.ffs_values:
			return 0
		# Remove old checkmarks
		if self.ffs_values == ():
			self.ffs_values = (None, None, None)
		font, face, size = self.ffs_values
		if font <> None:
			fnum = self.fontnames.index(font)
			self.fontitems[fnum].check(0)
		if face <> None:
			for i in range(len(self.faceitems)):
				if face & (1<<i):
					self.faceitems[i].check(0)
		if size <> None:
			for i in range(len(self.sizeitems)):
				if SIZES[i] == size:
					self.sizeitems[i].check(0)
				
		self.ffs_values = info
		# Set new checkmarks
		font, face, size = self.ffs_values
		if font <> None:
			fnum = self.fontnames.index(font)
			self.fontitems[fnum].check(1)
		if face <> None:
			for i in range(len(self.faceitems)):
				if face & (1<<i):
					self.faceitems[i].check(1)
		if size <> None:
			for i in range(len(self.sizeitems)):
				if SIZES[i] == size:
					self.sizeitems[i].check(1)
		# Set outline/normal for sizes
		if font:
			exists = getfontsizes(font, SIZES)
			for i in range(len(self.sizeitems)):
				if exists[i]:
					self.sizeitems[i].setstyle(0)
				else:
					self.sizeitems[i].setstyle(8)

	#
	# Apple menu
	#
	
	def do_about(self, id, item, window, event):
		EasyDialogs.Message("A simple single-font text editor based on WASTE")
			
	#
	# File menu
	#

	def open(self, *args):
		self._open(0)
		
	def openfile(self, *args):
		self._open(1)

	def _open(self, askfile):
		if askfile:
			fss, ok = macfs.StandardGetFile('TEXT')
			if not ok:
				return
			path = fss.as_pathname()
			name = os.path.split(path)[-1]
			try:
				fp = open(path, 'rb') # NOTE binary, we need cr as end-of-line
				data = fp.read()
				fp.close()
			except IOError, arg:
				EasyDialogs.Message("IOERROR: "+`arg`)
				return
		else:
			path = None
			name = "Untitled %d"%self.num
			data = ''
		w = WasteWindow(self)
		w.open(path, name, data)
		self.num = self.num + 1
		
	def closewin(self, *args):
		if self.active:
			self.active.close()
		else:
			EasyDialogs.Message("No active window?")
		
	def save(self, *args):
		if self.active:
			self.active.menu_save()
		else:
			EasyDialogs.Message("No active window?")
		
	def saveas(self, *args):
		if self.active:
			self.active.menu_save_as()
		else:
			EasyDialogs.Message("No active window?")
			
		
	def quit(self, *args):
		for w in self._windows.values():
			w.close()
		if self._windows:
			return
		self._quit()
		
	#
	# Edit menu
	#
	
	def undo(self, *args):
		if self.active:
			self.active.menu_undo()
		else:
			EasyDialogs.Message("No active window?")
		
	def cut(self, *args):
		if self.active:
			self.active.menu_cut()
		else:
			EasyDialogs.Message("No active window?")
		
	def copy(self, *args):
		if self.active:
			self.active.menu_copy()
		else:
			EasyDialogs.Message("No active window?")
		
	def paste(self, *args):
		if self.active:
			self.active.menu_paste()
		else:
			EasyDialogs.Message("No active window?")

	def clear(self, *args):
		if self.active:
			self.active.menu_clear()
		else:
			EasyDialogs.Message("No active window?")
		
	#
	# Other stuff
	#	

	def idle(self, event):
		if self.active:
			self.active.do_idle(event)
			
def getfontnames():
	names = []
	for i in range(256):
		n = Fm.GetFontName(i)
		if n: names.append(n)
	return names
	
def getfontsizes(name, sizes):
	exist = []
	num = Fm.GetFNum(name)
	for sz in sizes:
		if Fm.RealFont(num, sz):
			exist.append(1)
		else:
			exist.append(0)
	return exist

def main():
	App = Wed()
	App.mainloop()
	
if __name__ == '__main__':
	main()
	
