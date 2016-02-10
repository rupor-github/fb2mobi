#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import version
import traceback
import win_unicode_console

from modules.mobi_split import mobi_read

def process_file(infile, kindle_dir):

    if not os.path.exists(infile):
        print('File {0} not found'.format(infile))
        return

    print('Processing file {}'.format(infile))
    try:
        reader = mobi_read(infile)
        asin = reader.getASIN()
        if len(asin) > 0:
            thumb = reader.getThumbnail()
            if  thumb != None:
                thumb.convert('RGB').save(os.path.join(kindle_dir, 'thumbnail_' + asin + '_EBOK_portrait.jpg'), 'JPEG')
                print('Written thumbnail for {}'.format(asin))
            else:
                print("Skipping - no cover or thumbnail")
        else:
            print("Skipping - no ASIN")
    except:
        print('Error processing file.')
        traceback.print_exc()

    return

def process_folder(inputdir, outputdir=None):
    if outputdir:
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

    if os.path.isdir(inputdir):
        # let's see if we could locate kindle directory
        head = tail = inputdir
        while tail:
            head, tail = os.path.split(head)
            if tail:
                kindle_dir = os.path.join(head, 'system', 'thumbnails')
                if os.path.isdir(kindle_dir):
                    print('Found {}'.format(kindle_dir))
                    break
        else:
            print('Unable to find Kindle directory along the path "{0}"'.format(inputdir))
            sys.exit(-1)

        for root, dirs, files in os.walk(inputdir):
            for file in files:
                try:
                    if file.lower().endswith(('.mobi', '.azw3')):
                        inputfile = os.path.join(root, file)
                        process_file(inputfile, kindle_dir)
                except KeyboardInterrupt as e:
                    print('User interrupt. Exiting...')
                    sys.exit(-1)
                except IOError as e:
                    print('(I/O error {0}) {1} - {2}'.format(e.errno, e.strerror, e.filename))
                except:
                    traceback.print_exc()
    else:
        print('Unable to find directory "{0}"'.format(inputdir))
        sys.exit(-1)

def process(args):
    result = 0

    if args.inputdir:
        process_folder(args.inputdir)
    else:
        print(argparser.description)
        argparser.print_usage()

    return result


if __name__ == '__main__':

    win_unicode_console.enable()

    argparser = argparse.ArgumentParser(description='Sync covers for side-loaded books on Kindle. Version {0}'.format(version.VERSION))
    argparser.add_argument('-i', '--input-dir', dest='inputdir', type=str, default=None, help='Directory on device to look for books.')
    args = argparser.parse_args()

    process(args)
