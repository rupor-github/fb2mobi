# -*- coding: utf-8 -*-

import os
import sys
import shutil

import version

from slugify import slugify, smart_truncate


def make_dir(filename):
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)


def copy_file(src, dest):
    make_dir(dest)
    shutil.copyfile(src, dest)


def get_executable_path():
    if getattr(sys, 'frozen', False):
        executable_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    return executable_path


def get_executable_name():
    if getattr(sys, 'frozen', False):
        name, _ = os.path.splitext(os.path.basename((sys.executable)))
    else:
        name, _ = os.path.splitext(os.path.basename((sys.argv[0])))

    return name


def format_pattern(s, seq):

    def replace_keyword(pict, k, v):
        if pict.count(k) > 0:
            return pict.replace(k, v), True if v else False
        return pict, False

    def replace_keywords(pict, seq):
        expanded = False
        for (k, v) in seq:
            pict, ok = replace_keyword(pict, k, v)
            expanded = expanded or ok
        if not expanded:
            return ''
        return pict

    p_o = -1
    p_c = -1

    # Hack - I do not want to write real parser
    pps = s.replace(r'\{', chr(1)).replace(r'\}', chr(2))

    for i, sym in enumerate(pps):
        if sym == '{':
            p_o = i
        elif sym == '}':
            p_c = i
            break

    if p_o >= 0 and p_c > 0 and p_o < p_c:
        pps = format_pattern(pps[0:p_o] + replace_keywords(pps[p_o + 1:p_c], seq) + pps[p_c + 1:], seq)
    else:
        pps = replace_keywords(pps, seq)

    return pps.replace(chr(1), '{').replace(chr(2), '}')


# pylint: disable=C0330
windows_reserved = str.maketrans({
    '<': None,
    '>': None,
    ':': None,
    '"': None,
    '/': None,
    '\\': None,
    '|': None,
    '?': None,
    '*': None,
})


def clean_file_name(fname):

    if not os.path.supports_unicode_filenames:
        fname = slugify(fname, separator=' ')

    # Just in case - control path separators
    fname = fname.replace(os.sep, '')

    if version.WINDOWS:
        # Just in case
        fname = fname.translate(windows_reserved)
        # Seriously, I know that this is OLD Windows only, but...
        fname = smart_truncate(fname, max_length=260)

    return fname
