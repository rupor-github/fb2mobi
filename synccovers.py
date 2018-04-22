#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import argparse

import version

from modules.mobi_split import mobi_read

count_files = 0
count_located = 0
count_processed = 0


def process_file(infile, kindle_dir, width, height, stretch, verbose):

    global count_files, count_located, count_processed

    count_files += 1
    if not os.path.exists(infile):
        if verbose:
            print('WARNING: File {0} not found'.format(infile))
        return

    count_located += 1
    if verbose:
        print('Processing file {}'.format(infile))
    try:
        reader = mobi_read(infile, width, height, stretch)
        asin = reader.getCdeContentKey()
        if not asin:
            asin = reader.getASIN()
        if asin:
            thumb = reader.getThumbnail()
            if thumb != None:
                thumb.convert('RGB').save(os.path.join(kindle_dir, 'thumbnail_' + asin + '_' + reader.getCdeType() + '_portrait.jpg'), 'JPEG')
                count_processed += 1
                if verbose:
                    print('Written thumbnail for {}'.format(asin))
            else:
                if verbose:
                    print("Skipping - no cover or thumbnail")
        else:
            if verbose:
                print("Skipping - no ASIN")
    except:
        print('ERROR: processing file "{}".'.format(infile))
        # traceback.print_exc()

    return


def process_folder(inputdir, width, height, stretch, verbose):

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
            elif os.path.samefile(inputdir, head):
                # Possibly trailing path separator, try again, without it
                tail = head
        else:
            print('ERROR: unable to find Kindle system directory along the path "{0}"'.format(inputdir))
            sys.exit(-1)

        for root, dirs, files in os.walk(inputdir):
            for file in files:
                try:
                    if file.lower().endswith(('.mobi', '.azw3')):
                        inputfile = os.path.join(root, file)
                        process_file(inputfile, kindle_dir, width, height, stretch, verbose)
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


def read_thumbsize(s):
    w, h = 0, 0
    param = s.lower()
    if param.find('x') == -1:
        raise argparse.ArgumentTypeError('Wrong thumbsize format, should be one of WxH, Wx or xH')
    a = s.split('x')
    if a[0]:
        try:
            w = int(a[0])
        except ValueError:
            raise argparse.ArgumentTypeError('Wrong thumbsize format, width is not an integer')
    if a[1]:
        try:
            h = int(a[1])
        except ValueError:
            raise argparse.ArgumentTypeError('Wrong thumbsize format, height is not an integer')

    if w == 0 and h == 0:
        w, h = 33, 470
    elif w == 0:
        w = int(h // 1.6)
    elif h == 0:
        h = int(w * 1.6)

    return w, h


if __name__ == '__main__':

    argparser = argparse.ArgumentParser(description='Synchronize covers for side-loaded books on Kindle. Version {0}'.format(version.VERSION))
    argparser.add_argument('inputdir', type=str, nargs='?', default=None, help='Directory on mounted device to look for books.')
    argparser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Produce verbose output')
    argparser.add_argument('-s', '--thumbsize', dest='thumbsize', type=read_thumbsize, default='330x470', help='Size of resulting thumbnail (330x470)')
    argparser.add_argument('--stretch', dest='stretch', action='store_true', default=False, help='Do not preserve thumbnail aspect ratio')

    args = argparser.parse_args()

    if args.inputdir:
        process_folder(os.path.normpath(args.inputdir), args.thumbsize[0], args.thumbsize[1], args.stretch, args.verbose)
        print('\nTotal files {0}, located {1}, thumbnails written for {2}'.format(count_files, count_located, count_processed))
    else:
        print(argparser.description)
        argparser.print_usage()

    sys.exit(0)
