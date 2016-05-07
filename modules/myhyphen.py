# -*- coding: utf-8 -*-

import os, sys
import hyphen

DICTIONARIES_DIR = os.path.join(os.path.abspath(os.path.dirname(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(__file__), 'dictionaries')

SOFT_HYPHEN = '\u00AD'
NON_BREAKING_SPACE = '\u00A0'

WORD_SEPARATORS = [' ', NON_BREAKING_SPACE, '-', '.', ',', ';', ':', '!', '?']


class MyHyphen:
    def __init__(self, language):
        self.hyphenator = hyphen.Hyphenator(language=language, directory=DICTIONARIES_DIR)

    def process_text(self, text, replace_nbsp, separators):
        if not separators:
            syl = self.hyphenator.syllables(text)
            return text if not syl else SOFT_HYPHEN.join(syl)
        else:
            res = []
            head, *tail = separators
            for part in str.split(text, head):
                res.append(self.process_text(part, replace_nbsp, tail))
            head = head if not replace_nbsp or not head == NON_BREAKING_SPACE else ' '
            return head.join(res)

    def set_language(self, language):
        self.hyphenator = hyphen.Hyphenator(language=language, directory=DICTIONARIES_DIR)

    def hyphenate_text(self, text, replace_nbsp=False):
        return self.process_text(text, replace_nbsp, WORD_SEPARATORS)
