This program is based on fb2conv program published by [dnkorpushov](https://github.com/dnkorpushov) on [the-ebook.org](http://www.the-ebook.org/forum/viewtopic.php?t=28447) site.

Original program (being Python 2) did not work well under Windows when non-russian system codepage was selected for non-Unicode programs. 
In order to improve the situation I had to port it to Python 3. Later author of original converter re-joined the project and ported GUI UI here. 
He also added binary GUI releases for MAC.

Here is brief list of changes to the original project (in addition to bug fixes):

* All messages and profile descriptions got translated to English
* Fixed all problems I was aware of at the moment (see git log)
* Added ability to apply xslt transformation from external file to fb2 before further processing (`--xslt` key or `<xslt>` config tag)
* Added xslt extension "katz_tr" to speedup and simplify transformation of direct speech in dialogs
* Added smart dropcaps processing (`--dropcaps=Smart` key or `<dropcaps>Smart</dropcaps>` config tag)
* Added some rudimentary epub processing (like title rewriting based on calibre metadata and hyphenation)
* Switched hyphenator to hyphen which uses properly maintained dictionaries from LibreOffice, so now many languages are supported and you could add more
* Added support for "floating" footnotes (`--notes-mode=float` key or `<notesMode>float</notesMode>` config tag)
* Added support for MOBI post-processing and optimization
* Added cover and thumbnail image optimization
* Made cover size user configurable (`--screen-width`, `--screen-height` or `<screenWidth>`, `<screenHeight>`)
* Added support for latest Kidle firmware (>= 5.7.2)
* Added simple tool to generate thumbnails on Kindle devices
* Added synchronous logging to file and console (console logging level is set independently by `--console-level` key or `<consoleLevel>` config tag)
* Added an option to make PNG images non-transparent to prevent "ghostly images" on Kindle (`--remove-png-transparency` key or `<removePngTransparency>` config tag)
* Added support for auto-generation of PageMaps - now it is possible to have APNX files (`--apnx=eInk|PC` key or `<generateAPNX>` profile tag). Number of uncompessed 
  text characters per page is (aproximatly) controlled by `charactersPerPage` profile tag and by default is equal to 2300 (as in Calibre)
* Removed `<flatTOC>` support. New config tag `<tocType>` and command line parameter `--toc-type` could be used instead with values `Flat|Kindle|Normal`.
  This introduces special support for eInk Kindle devices with 2-level TOC views. Additional tag `<tocKindleLevel>` and parameter `--toc-kindle-level` allow for precise 
  tuning of generated NCX for eInk devices.
* Expanded book title generation: added `#padnumber` to generate number in series padded with zeros (use `<seriesPositions>` or `--series-positions` to specify how many
  digits overall will be generated) and `#date` to add proper date from `<title-info>` if availabe.
* Added new `<chapterLevel>` configuration tag and `---chapter-level` parameter along with new style `.titleblock_nobreak`. When parsing sections this style will be generated
  if nesting level is greater or equal to specified value. This allows better control of page breaks on sections boundaries.
* Supported `<openBookFromCover>` configuration tag and `---open-book-from-cover` parameter for compatibility with fb2conv
* Changed how book title and book author are formatted - added processing of conditional blocks ex: `<bookTitleFormat>{(#abbrseries{ #padnumber}) }#title</bookTitleFormat>`

More info can be found on [russian forum](http://www.the-ebook.org/forum/viewtopic.php?t=30380).

Program uses source code (modified) from following projects released under GPL:

* [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)

In order to build [releases](https://github.com/rupor-github/fb2mobi/releases) we are using Python 3.6.0, [cx_Freeze 5.0.1](https://bitbucket.org/anthony_tuininga/cx_freeze) and following libraries:

* cssutils-1.0.1
* lxml-3.7.1
* Pillow-4.0.0
* PyHyphen [fork with fixes (2.0.6):](https://github.com/rupor-github/pyhyphen)
  * on all platforms usage of Python 3.6 pymalloc interface in hjn module corrupts Python heap and prevents converter from working
  * on Windows PyHyphen 2.0.5 does not handle Unicode path names, which prevents converter from working when installed in directories with localized names
* PyQt 5.71 (for GUI versions)

If you are not using "frozen" distribution you would need to download [Amazon's KindleGen](https://www.amazon.com/gp/feature.html?docId=1000765211).
If you are using converter as a companion to [MyHomeLib](http://home-lib.net/) you only need command line (CLI) version(s).

Enjoy!
