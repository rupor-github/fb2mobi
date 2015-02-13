# -*- coding: utf-8 -*- 
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

class CustomListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.SIMPLE_BORDER)
        ListCtrlAutoWidthMixin.__init__(self)
