#!/usr/bin/env python
#coding=utf-8
"""
Hyphenation, using Frank Liang's algorithm.

Ned Batchelder, July 2007.
This Python code is in the public domain.

Not English hyphenation patterns and code changes added by Denis Malinovsky,
2012-2013.
"""

from importlib import import_module
import re

class Hyphenator:
    def __init__(self, lang):
        self.tree = {}
        self.exceptions = {}
        # Load corresponding hyphenation patterns, using Russian as a fallback
        try:
            self._load_language(lang)
        except ImportError:
            lang = 'ru'
            self._load_language(lang)
        if lang == 'ru':
            # Russian texts often require English hyphenation as well
            self._load_language('en')

    def _init_patterns(self, patterns, exceptions):
        for pattern in patterns.split():
            self._insert_pattern(pattern)

        for ex in exceptions.split():
            # Convert the hyphenated pattern into a point array for use later.
            self.exceptions[ex.replace('-', '')] = [0] + [ int(h == '-') for h in re.split(r'[\w]', ex, flags=re.U) ]

    def _insert_pattern(self, pattern):
        # Convert the a pattern like 'a1bc3d4' into a string of chars 'abcd'
        # and a list of points [ 1, 0, 3, 4 ].
        chars = re.sub('[0-9]', '', pattern)
        points = [ int(d or 0) for d in re.split(u'[^0-9]', pattern, flags=re.U) ]

        # Insert the pattern into the tree.  Each character finds a dict
        # another level down in the tree, and leaf nodes have the list of
        # points.
        t = self.tree
        for c in chars:
            if c not in t:
                t[c] = {}
            t = t[c]
        t[None] = points

    def _load_language(self, lang):
        module = import_module('hyphenations.%s' % lang)
        self._init_patterns(module.patterns, module.exceptions)

    def hyphenate_word(self, word, separator='-'):
        """Returns a word with separators inserted as hyphens."""
        result = u''
        buf = u''
        word += u'$'
        for c in word:
            # Split URls: example.com/-test/-page.html
            if c.isalpha() or (c == u'/' and buf):
                buf += c
            else:
                if len(buf):
                    result += separator.join(self._hyphenate_word(buf))
                buf = ''
                result += c
        result = result[:-1]
        return result

    def _hyphenate_word(self, word):
        """ Given a word, returns a list of pieces, broken at the possible
            hyphenation points.
        """
        # Short words aren't hyphenated.
        if len(word) <= 3:
            return [word]
        # rupor - just in case HTML entities aren't hyphenated
        if word.startswith('&') and word.endswith(';'):
            return [word]
        # If the word is an exception, get the stored points.
        if word.lower() in self.exceptions:
            points = self.exceptions[word.lower()]
        else:
            work = '.' + word.lower() + '.'
            points = [0] * (len(work)+1)
            for i in range(len(work)):
                t = self.tree
                for c in work[i:]:
                    if c in t:
                        t = t[c]
                        if None in t:
                            p = t[None]
                            for j in range(len(p)):
                                points[i+j] = max(points[i+j], p[j])
                    else:
                        break
            # No hyphens in the first two chars or the last two.
            points[1] = points[2] = points[-2] = points[-3] = 0

        # Examine the points to build the pieces list.
        pieces = ['']
        for c, p in zip(word, points[2:]):
            pieces[-1] += c
            if p % 2 and c != '-':
                pieces.append('')
        return pieces

if __name__ == '__main__':
    import sys
    hyphenator = Hyphenator('ru')
    if len(sys.argv) > 1:
        for word in sys.argv[1:]:
            print(hyphenator.hyphenate_word(unicode(word, 'utf-8')))
    else:
        import doctest
        doctest.testmod(verbose=True)
