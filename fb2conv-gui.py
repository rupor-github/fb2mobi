#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
from uiMainFrame import uiMainFrame

class MyApp(wx.App):
	def __init__(self):
		wx.App.__init__(self)
		self.Bind(wx.wx.EVT_ACTIVATE_APP, self.OnActivate)

	def OnInit(self):
		frame = uiMainFrame(None)
		frame.Show()

		return True

	def BringWindowToFront(self):
		try:
			self.GetTopWindow().Raise()
		except:
			pass

	def OnActivate(self, event):
		if event.GetActive():
			self.BringWindowToFront()
		event.Skip()


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
