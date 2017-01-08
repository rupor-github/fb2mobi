This program is based on fb2conv program published by dnkorpushov on [the-ebook.org](http://www.the-ebook.org/forum/viewtopic.php?t=28447) site.

Original program (being Python 2) did not work well under Windows when non-russian system codepage was selected for non-Unicode programs. 
In order to improve the situation I had to port it to Python 3. As I am only using it as a companion converter from [MyHomeLib](http://home-lib.net/) 
it lost number of features and gained some bug fixes...

Here is brief list of changes:

* Lost UI functionality
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

More info can be found on [russian forum](http://www.the-ebook.org/forum/viewtopic.php?t=30380).

Program uses source code (modified) from following projects released under GPL and MIT licenses:

* [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)
* [win-unicode-console](https://github.com/Drekin/win-unicode-console)

In order to build [Windows releases](https://github.com/rupor-github/fb2mobi/releases) I am using Python 3.6.0, [cx_Freeze 5.0.1](https://bitbucket.org/anthony_tuininga/cx_freeze) and following libraries:

* cssutils-1.0.1
* lxml-3.7.1
* Pillow-4.0.0
* PyHyphen-2.0.5 
  * on Windows PyHyphen 2.0.5 does not handle Unicode path names, which prevents converter to work properly when installed in directories with localized names (Use https://github.com/rupor-github/pyhyphen 2.0.6 instead if necessary)
  * on Windows usage of Python 3.6 pymalloc interface in hjn corrupts Python heap and prevents program from working (Use https://github.com/rupor-github/pyhyphen 2.0.6 instead if necessary)

If you are not on Windows and/or not using "frozen" distribution you would need to download [Amazon's KindleGen](https://www.amazon.com/gp/feature.html?docId=1000765211).

Enjoy!
