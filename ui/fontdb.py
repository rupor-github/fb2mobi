#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os
from PIL import ImageFont

class FontDb(object):	
	def __init__(self, path):
		self.fonts_path = path
		self.families = {}
		self.update_db()

	def update_db(self):
		self.families = {}
		
		if os.path.isdir(self.fonts_path):
			for file in os.listdir(self.fonts_path):
				if os.path.splitext(file)[1].lower() in ['.ttf', '.otf']:
					font_file = os.path.join(self.fonts_path, file)
					try:
						font = ImageFont.truetype(font_file, 10)
						if font.font.family not in self.families:
							self.families[font.font.family] = {}
						self.families[font.font.family][font.font.style] = file
					except:
						# Not a font file
						pass


		