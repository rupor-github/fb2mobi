# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Nov  6 2013)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
from CustomListCtrl import CustomListCtrl

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"fb2conv-gui", pos = wx.DefaultPosition, size = wx.Size( 685,505 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel2 = wx.Panel( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer2 = wx.FlexGridSizer( 0, 1, 0, 0 )
		fgSizer2.AddGrowableCol( 0 )
		fgSizer2.AddGrowableRow( 1 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		fgSizer3 = wx.FlexGridSizer( 3, 2, 0, 0 )
		fgSizer3.AddGrowableCol( 1 )
		fgSizer3.SetFlexibleDirection( wx.BOTH )
		fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText1 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Профиль конвертера", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		fgSizer3.Add( self.m_staticText1, 0, wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		fgSizer7 = wx.FlexGridSizer( 0, 3, 0, 0 )
		fgSizer7.AddGrowableCol( 0 )
		fgSizer7.AddGrowableRow( 0 )
		fgSizer7.SetFlexibleDirection( wx.BOTH )
		fgSizer7.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		choiceProfileChoices = []
		self.choiceProfile = wx.Choice( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceProfileChoices, 0 )
		self.choiceProfile.SetSelection( 0 )
		fgSizer7.Add( self.choiceProfile, 1, wx.EXPAND|wx.BOTTOM, 5 )
		
		self.m_staticText3 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Формат", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer7.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.LEFT, 5 )
		
		choiceFormatChoices = [ u"epub", u"mobi", u"azw3" ]
		self.choiceFormat = wx.Choice( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choiceFormatChoices, 0 )
		self.choiceFormat.SetSelection( 0 )
		fgSizer7.Add( self.choiceFormat, 0, wx.BOTTOM|wx.LEFT, 5 )
		
		
		fgSizer3.Add( fgSizer7, 1, wx.EXPAND, 5 )
		
		self.m_staticText2 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Конвертировать в папку", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		fgSizer3.Add( self.m_staticText2, 0, wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		
		fgSizer5 = wx.FlexGridSizer( 1, 3, 0, 0 )
		fgSizer5.AddGrowableCol( 0 )
		fgSizer5.SetFlexibleDirection( wx.BOTH )
		fgSizer5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.textOutputDir = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer5.Add( self.textOutputDir, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND, 5 )
		
		self.buttonSelectDir = wx.Button( self.m_panel2, wx.ID_ANY, u"Выбрать...", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer5.Add( self.buttonSelectDir, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.LEFT, 5 )
		
		self.buttonOpenOutputDir = wx.BitmapButton( self.m_panel2, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW )
		self.buttonOpenOutputDir.SetToolTipString( u"Показать папку" )
		
		fgSizer5.Add( self.buttonOpenOutputDir, 1, wx.BOTTOM|wx.LEFT|wx.EXPAND, 5 )
		
		
		fgSizer3.Add( fgSizer5, 1, wx.EXPAND, 5 )
		
		
		fgSizer3.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.checkConvertToSourceDir = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Конвертировать в исходную папку", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer3.Add( self.checkConvertToSourceDir, 0, wx.BOTTOM, 5 )
		
		
		fgSizer2.Add( fgSizer3, 1, wx.EXPAND, 10 )
		
		self.listFiles = CustomListCtrl(self.m_panel2)
		fgSizer2.Add( self.listFiles, 1, wx.EXPAND|wx.BOTTOM, 5 )
		
		self.m_panel3 = wx.Panel( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer4 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer4.AddGrowableCol( 0 )
		fgSizer4.AddGrowableRow( 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.gaugeProgress = wx.Gauge( self.m_panel3, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 200,-1 ), wx.GA_HORIZONTAL )
		self.gaugeProgress.SetValue( 0 ) 
		fgSizer4.Add( self.gaugeProgress, 1, wx.BOTTOM|wx.EXPAND|wx.LEFT|wx.RESERVE_SPACE_EVEN_IF_HIDDEN|wx.RIGHT, 5 )
		
		self.buttonStart = wx.Button( self.m_panel3, wx.ID_ANY, u"Старт", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer4.Add( self.buttonStart, 0, wx.BOTTOM|wx.LEFT, 5 )
		
		
		self.m_panel3.SetSizer( fgSizer4 )
		self.m_panel3.Layout()
		fgSizer4.Fit( self.m_panel3 )
		fgSizer2.Add( self.m_panel3, 1, wx.EXPAND, 5 )
		
		
		self.m_panel2.SetSizer( fgSizer2 )
		self.m_panel2.Layout()
		fgSizer2.Fit( self.m_panel2 )
		bSizer2.Add( self.m_panel2, 1, wx.EXPAND|wx.ALL, 15 )
		
		
		self.m_panel1.SetSizer( bSizer2 )
		self.m_panel1.Layout()
		bSizer2.Fit( self.m_panel1 )
		bSizer1.Add( self.m_panel1, 1, wx.EXPAND, 10 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.menuFile = wx.Menu()
		self.menuFileAdd = wx.MenuItem( self.menuFile, wx.ID_OPEN, u"Добавить..."+ u"\t" + u"Ctrl+O", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuFile.AppendItem( self.menuFileAdd )
		
		self.menuFileConvert = wx.MenuItem( self.menuFile, wx.ID_ANY, u"Конвертировать", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuFile.AppendItem( self.menuFileConvert )
		
		self.menuFileExit = wx.MenuItem( self.menuFile, wx.ID_EXIT, u"Выход", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuFile.AppendItem( self.menuFileExit )
		
		self.m_menubar1.Append( self.menuFile, u"Файл" ) 
		
		self.menuEdit = wx.Menu()
		self.menuEditSelectAll = wx.MenuItem( self.menuEdit, wx.ID_SELECTALL, u"Выделить все"+ u"\t" + u"Ctrl+A", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuEdit.AppendItem( self.menuEditSelectAll )
		
		self.menuEditDelete = wx.MenuItem( self.menuEdit, wx.ID_DELETE, u"Удалить", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuEdit.AppendItem( self.menuEditDelete )
		
		self.menuEditDeleteSuccess = wx.MenuItem( self.menuEdit, wx.ID_ANY, u"Удалить успешно завершенные", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuEdit.AppendItem( self.menuEditDeleteSuccess )
		
		self.menuEdit.AppendSeparator()
		
		self.menuEditViewLog = wx.MenuItem( self.menuEdit, wx.ID_ANY, u"Просмотреть журнал", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuEdit.AppendItem( self.menuEditViewLog )
		
		self.m_menubar1.Append( self.menuEdit, u"Правка" ) 
		
		self.menuHelp = wx.Menu()
		self.menuHelpSupport = wx.MenuItem( self.menuHelp, wx.ID_ANY, u"Форум поддержки", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuHelp.AppendItem( self.menuHelpSupport )
		
		self.menuHelpAbout = wx.MenuItem( self.menuHelp, wx.ID_ABOUT, u"О программе...", wx.EmptyString, wx.ITEM_NORMAL )
		self.menuHelp.AppendItem( self.menuHelpAbout )
		
		self.m_menubar1.Append( self.menuHelp, u"Справка" ) 
		
		self.SetMenuBar( self.m_menubar1 )
		
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.MainWindowOnClose )
		self.textOutputDir.Bind( wx.EVT_KILL_FOCUS, self.textOutputDirOnKillFocus )
		self.buttonSelectDir.Bind( wx.EVT_BUTTON, self.buttonSelectDirOnCLick )
		self.buttonOpenOutputDir.Bind( wx.EVT_BUTTON, self.buttonOpenOutputDirOnClick )
		self.checkConvertToSourceDir.Bind( wx.EVT_CHECKBOX, self.onCheckConvertToSourceDir )
		self.buttonStart.Bind( wx.EVT_BUTTON, self.buttonStartOnClick )
		self.Bind( wx.EVT_MENU, self.menuFileAddOnSelect, id = self.menuFileAdd.GetId() )
		self.Bind( wx.EVT_MENU, self.menuFileConvertOnSelect, id = self.menuFileConvert.GetId() )
		self.Bind( wx.EVT_MENU, self.menuFileExitOnSelect, id = self.menuFileExit.GetId() )
		self.Bind( wx.EVT_MENU, self.menuEditSelectAllOnSelect, id = self.menuEditSelectAll.GetId() )
		self.Bind( wx.EVT_MENU, self.menuEditDeleteOnSelect, id = self.menuEditDelete.GetId() )
		self.Bind( wx.EVT_MENU, self.menuEditDeleteSuccessOnSelect, id = self.menuEditDeleteSuccess.GetId() )
		self.Bind( wx.EVT_MENU, self.menuEditViewLogOnSelect, id = self.menuEditViewLog.GetId() )
		self.Bind( wx.EVT_MENU, self.menuHelpSupportOnSelect, id = self.menuHelpSupport.GetId() )
		self.Bind( wx.EVT_MENU, self.menuHelpAboutOnSelect, id = self.menuHelpAbout.GetId() )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def MainWindowOnClose( self, event ):
		event.Skip()
	
	def textOutputDirOnKillFocus( self, event ):
		event.Skip()
	
	def buttonSelectDirOnCLick( self, event ):
		event.Skip()
	
	def buttonOpenOutputDirOnClick( self, event ):
		event.Skip()
	
	def onCheckConvertToSourceDir( self, event ):
		event.Skip()
	
	def buttonStartOnClick( self, event ):
		event.Skip()
	
	def menuFileAddOnSelect( self, event ):
		event.Skip()
	
	def menuFileConvertOnSelect( self, event ):
		event.Skip()
	
	def menuFileExitOnSelect( self, event ):
		event.Skip()
	
	def menuEditSelectAllOnSelect( self, event ):
		event.Skip()
	
	def menuEditDeleteOnSelect( self, event ):
		event.Skip()
	
	def menuEditDeleteSuccessOnSelect( self, event ):
		event.Skip()
	
	def menuEditViewLogOnSelect( self, event ):
		event.Skip()
	
	def menuHelpSupportOnSelect( self, event ):
		event.Skip()
	
	def menuHelpAboutOnSelect( self, event ):
		event.Skip()
	

###########################################################################
## Class DialogAbout
###########################################################################

class DialogAbout ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"О программе", pos = wx.DefaultPosition, size = wx.Size( 493,258 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer7 = wx.FlexGridSizer( 2, 1, 0, 0 )
		fgSizer7.AddGrowableCol( 0 )
		fgSizer7.AddGrowableRow( 0 )
		fgSizer7.SetFlexibleDirection( wx.BOTH )
		fgSizer7.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		bSizer4 = wx.BoxSizer( wx.VERTICAL )
		
		fgSizer8 = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizer8.AddGrowableCol( 1 )
		fgSizer8.AddGrowableRow( 0 )
		fgSizer8.SetFlexibleDirection( wx.BOTH )
		fgSizer8.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.bitmapIcon = wx.StaticBitmap( self.m_panel4, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size( 128,128 ), 0 )
		fgSizer8.Add( self.bitmapIcon, 0, wx.ALL, 5 )
		
		fgSizer9 = wx.FlexGridSizer( 3, 1, 0, 0 )
		fgSizer9.AddGrowableCol( 0 )
		fgSizer9.SetFlexibleDirection( wx.BOTH )
		fgSizer9.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.staticText1 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"fb2conv", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticText1.Wrap( -1 )
		self.staticText1.SetFont( wx.Font( 16, 70, 90, 90, False, wx.EmptyString ) )
		
		fgSizer9.Add( self.staticText1, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText5 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Конвертер файлов формата fb2 в epub, mobi, azw3", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		fgSizer9.Add( self.m_staticText5, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText6 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Автор: dnk_dz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		fgSizer9.Add( self.m_staticText6, 0, wx.ALL, 5 )
		
		
		fgSizer8.Add( fgSizer9, 1, wx.EXPAND, 5 )
		
		
		bSizer4.Add( fgSizer8, 1, wx.EXPAND, 5 )
		
		
		fgSizer7.Add( bSizer4, 1, wx.EXPAND, 5 )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		self.buttonOk = wx.Button( self.m_panel4, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.buttonOk, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 5 )
		
		
		fgSizer7.Add( bSizer5, 1, wx.EXPAND, 5 )
		
		
		self.m_panel4.SetSizer( fgSizer7 )
		self.m_panel4.Layout()
		fgSizer7.Fit( self.m_panel4 )
		bSizer3.Add( self.m_panel4, 1, wx.EXPAND|wx.ALL, 15 )
		
		
		self.SetSizer( bSizer3 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.buttonOk.Bind( wx.EVT_BUTTON, self.buttonOkOnClick )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def buttonOkOnClick( self, event ):
		event.Skip()
	

