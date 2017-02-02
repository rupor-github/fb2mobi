#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from lxml import etree
from lxml.builder import E
import os
import codecs

class GuiConfig():
	def __init__(self, config_file):
		self.config_file = os.path.normpath(os.path.abspath(config_file))

		self.lastUsedProfile = None
		self.lastUsedFormat = None
		self.outputFolder = None
		self.convertToSourceDirectory = False
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
			if e.tag == 'lastUsedProfile':
				self.lastUsedProfile = e.text

			elif e.tag == 'lastUsedFormat':
				self.lastUsedFormat = e.text

			elif e.tag == 'outputFolder':
				self.outputFolder = e.text

			elif e.tag == 'convertToSourceDirectory':
				self.convertToSourceDirectory = e.text.lower() == 'true'
			elif e.tag == 'geometry':
				for g in e:
					self.geometry[g.tag] = int(g.text) if g.text else None
			


	def write(self):
		config = E('settings',
					E('lastUsedProfile', self.lastUsedProfile) if self.lastUsedProfile else E('lastUsedProfile'),
					E('lastUsedFormat', self.lastUsedFormat) if self.lastUsedFormat else E('lastUsedFormat'),
					E('outputFolder', self.outputFolder) if self.outputFolder else E('outputFolder'),
					E('convertToSourceDirectory', str(self.convertToSourceDirectory)),
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

