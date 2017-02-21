#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from lxml import etree
from lxml.builder import E
import os
import codecs

class GuiConfig():
	def __init__(self, config_file):
		self.config_file = os.path.normpath(os.path.abspath(config_file))

		self.converterConfig = {}
		self.currentProfile = None
		self.currentFormat = None
		self.outputFolder = None
		self.convertToSourceDirectory = False
		self.hyphens = None
		self.kindlePath = None
		self.kindleCopyToDevice = False
		self.kindleSyncCovers = False
		self.lastUsedPath = None

		self.columns = {}
		self.columns['0'] = None
		self.columns['1'] = None
		self.columns['2'] = None

		self.geometry = {}
		self.geometry['x'] = None
		self.geometry['y'] = None
		self.geometry['width'] = None
		self.geometry['height'] = None

		if not os.path.exists(self.config_file):
			self.write()

		self.load()


	def load(self):
		config = etree.parse(self.config_file)
		for e in config.getroot():
			if e.tag == 'currentProfile':
				self.currentProfile = e.text

			elif e.tag == 'currentFormat':
				self.currentFormat = e.text

			elif e.tag == 'outputFolder':
				self.outputFolder = e.text

			elif e.tag == 'hyphens':
				self.hyphens = e.text

			elif e.tag == 'lastUsedPath':
				self.lastUsedPath = e.text

			elif e.tag == 'kindlePath':
				self.kindlePath = e.text

			elif e.tag == 'kindleCopyToDevice':
				self.kindleCopyToDevice = e.text.lower() == 'true'

			elif e.tag == 'kindleSyncCovers':
				self.kindleSyncCovers = e.text.lower() == 'true'

			elif e.tag == 'convertToSourceDirectory':
				self.convertToSourceDirectory = e.text.lower() == 'true'
			elif e.tag == 'columns':
				for c in e:
					self.columns[c.tag[1:]] = int(c.text) if c.text else None
			elif e.tag == 'geometry':
				for g in e:
					self.geometry[g.tag] = int(g.text) if g.text else None
			


	def write(self):
		config = E('settings',
					E('currentProfile', self.currentProfile) if self.currentProfile else E('currentProfile'),
					E('currentFormat', self.currentFormat) if self.currentFormat else E('currentFormat'),
					E('hyphens', self.hyphens) if self.hyphens else E('hyphens'),
					E('outputFolder', self.outputFolder) if self.outputFolder else E('outputFolder'),
					E('lastUsedPath', self.lastUsedPath) if self.lastUsedPath else E('lastUsedPath'),
					E('convertToSourceDirectory', str(self.convertToSourceDirectory)),
					E('kindlePath', self.kindlePath) if self.kindlePath else E('kindlePath'),
					E('kindleCopyToDevice', str(self.kindleCopyToDevice)),
					E('kindleSyncCovers', str(self.kindleSyncCovers)),
					E('columns',
						E('c0', str(self.columns['0'])) if self.columns['0'] else E('c0'),
						E('c1', str(self.columns['1'])) if self.columns['1'] else E('c1'),
						E('c2', str(self.columns['2'])) if self.columns['2'] else E('c2')
						),
					E('geometry',
						E('x', str(self.geometry['x'])) if self.geometry['x'] else E('x'),
						E('y', str(self.geometry['y'])) if self.geometry['y'] else E('y'),
						E('width', str(self.geometry['width'])) if self.geometry['width'] else E('width'),
						E('height', str(self.geometry['height'])) if self.geometry['height'] else E('height')
						)
					)
		config_dir = os.path.dirname(self.config_file)
		if not os.path.exists(config_dir):
			os.makedirs(config_dir)
			
		with codecs.open(self.config_file, "wb") as f:
			f.write(etree.tostring(config, encoding="utf-8", pretty_print=True, xml_declaration=True))
			f.close()


if __name__ == '__main__':
	gui_config = GuiConfig('fb2mobi-gui.config')
	gui_config.write()

