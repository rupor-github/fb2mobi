#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, traceback

import argparse
import version

from modules.mobi_split import mobi_read

count_files = 0
count_located = 0
count_processed = 0

def process_file(infile, kindle_dir, verbose):

    global count_files, count_located, count_processed

    count_files += 1
    if not os.path.exists(infile):
        if verbose: print('WARNING: File {0} not found'.format(infile))
        return

    count_located += 1
    if verbose: print('Processing file {}'.format(infile))
    try:
        reader = mobi_read(infile)
        asin = reader.getASIN()
        if len(asin) > 0:
            thumb = reader.getThumbnail()
            if thumb != None:
                thumb.convert('RGB').save(os.path.join(kindle_dir, 'thumbnail_' + asin + '_EBOK_portrait.jpg'), 'JPEG')
                count_processed += 1
                if verbose: print('Written thumbnail for {}'.format(asin))
            else:
                if verbose: print("Skipping - no cover or thumbnail")
        else:
            if verbose: print("Skipping - no ASIN")
    except:
        print('ERROR: processing file.')
        traceback.print_exc()

    return


def process_folder(inputdir, verbose):

    if os.path.isdir(inputdir):
        # let's see if we could locate kindle directory
        head = tail = inputdir
        while tail:
            head, tail = os.path.split(head)
            if tail:
                kindle_dir = os.path.join(head, 'system', 'thumbnails')
                if os.path.isdir(kindle_dir):
                    print('Found Kindle thumbnails directory "{}"'.format(kindle_dir))
                    break
        else:
            print('ERROR: unable to find Kindle system directory along the path "{0}"'.format(inputdir))
            sys.exit(-1)

        for root, dirs, files in os.walk(inputdir):
            for file in files:
                try:
                    if file.lower().endswith(('.mobi', '.azw3')):
                        inputfile = os.path.join(root, file)
                        process_file(inputfile, kindle_dir, verbose)
                except KeyboardInterrupt as e:
                    print('User interrupt. Exiting...')
                    sys.exit(-1)
                except IOError as e:
                    print('ERROR: I/O {0}: {1} - {2}'.format(e.errno, e.strerror, e.filename))
                except:
                    traceback.print_exc()
    else:
        print('ERROR: unable to find input directory "{0}"'.format(inputdir))
        sys.exit(-1)


if __name__ == '__main__':

    if sys.platform == "win32":
        class UniStream(object):
            __slots__ = ("fileno", "softspace",)

            def __init__(self, fileobject):
                self.fileno = fileobject.fileno()
                self.softspace = False
            def write(self, text):
                os.write(self.fileno, text.encode("utf-8", errors='ignore'))
            def flush(self):
                pass

        sys.stdout = UniStream(sys.stdout)
        sys.stderr = UniStream(sys.stderr)

    argparser = argparse.ArgumentParser(description='Synchronize covers for side-loaded books on Kindle. Version {0}'.format(version.VERSION))
    argparser.add_argument('inputdir', type=str, nargs='?', default=None,  help='Directory on mounted device to look for books.')
    argparser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Produce verbose output')

    args = argparser.parse_args()

    if args.inputdir:
        process_folder(args.inputdir, args.verbose)
        print('\nTotal files {0}, located {1}, thumbnails written for {2}'.format(count_files, count_located, count_processed))
    else:
        print(argparser.description)
        argparser.print_usage()

    sys.exit(0)
