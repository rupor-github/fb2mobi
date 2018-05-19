This program is based on fb2conv program published by [dnkorpushov](https://github.com/dnkorpushov) on [the-ebook.org](http://www.the-ebook.org/forum/viewtopic.php?t=28447) site.

Original program (being Python 2) did not work well under Windows when non-russian system codepage was selected for non-Unicode programs.
In order to improve the situation I had to port it to Python 3. Later author of original converter re-joined the project and ported GUI UI here.
He also added binary releases for MAC.

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
  text characters per page is (approximately) controlled by `charactersPerPage` profile tag and by default is equal to 2300 (Calibre default setting)
* Removed `<flatTOC>` support. New config tag `<tocType>` and command line parameter `--toc-type` could be used instead with values `Flat|Kindle|Normal`.
  This introduces special support for eInk Kindle devices with 2-level TOC views. Additional tag `<tocKindleLevel>` and parameter `--toc-kindle-level` allow for precise
  tuning of generated NCX for eInk devices.
* Expanded book title generation: added `#padnumber` to generate number in series padded with zeros (use `<seriesPositions>` or `--series-positions` to specify how many
  digits overall will be generated) and `#date` to add proper date from `<title-info>` if availabe.
* Added new `<chapterLevel>` configuration tag and `---chapter-level` parameter along with new style `.titleblock_nobreak`. When parsing sections this style will be generated
  if nesting level is greater or equal to specified value. This allows better control of page breaks on sections boundaries.
* Supported `<openBookFromCover>` configuration tag and `---open-book-from-cover` parameter for compatibility with fb2conv. Works for `epub` output only.
* Changed how book title and book author are formatted - added processing of conditional blocks, for example: `<bookTitleFormat>{(#abbrseries{ #padnumber}) }#title</bookTitleFormat>`. To output curly braces escape them with backslash.
* Added new css style `.linkanchor` - this is style for all href links which are NOT pointing to the note bodies. This allows for flexible formatting of hyperlinks in the text.
* Added "default" cover for fb2 which do not have it (APG 2018.1) - `<coverDefault>` in profile configuration.
* Added image re-sampling - `<scaleImages>` in profile configuration or `--scale-images` on command line (Should be positive non-zero float number, cover image is exempt from this). DPI is preserved.
* Added `--config` parameter and changed the way program looks for configuration file. Now, unless --config is provided files in user HOME directory have precedence over distribution files.
* For FB2 input files output name could be derived from book metadata using tag `<outputPattern>` and the same rules as for book title.
* Added support for multiple authors

More info can be found on [russian forum](http://www.the-ebook.org/forum/viewtopic.php?t=30380).

Program uses source code (modified) from following projects released under GPL:

* [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)
* [Image Utils](https://gist.github.com/drcongo/8521040)

In order to build [releases](https://github.com/rupor-github/fb2mobi/releases) we are using Python 3.6.5 with [following modules](https://github.com/rupor-github/fb2mobi/blob/master/requirements.txt).

If you are not using "frozen" distribution you would need to download [Amazon's KindleGen](https://www.amazon.com/gp/feature.html?docId=1000765211).

Enjoy!
