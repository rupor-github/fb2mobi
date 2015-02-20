This program is based on fb2conv program published by dnkorpushov on [the-ebook.org](http://www.the-ebook.org/forum/viewtopic.php?t=28447&postdays=0&postorder=asc&start=0) site.

Original program (being Python 2) did not work well under Windows when non-russian system codepage was selected for non-Unicode programs. 
In order to improve the situation I had to port it to Python 3 (3.4.2 at the moment). As I am only using it as a companion converter from [MyHomeLib](http://home-lib.net/) 
it lost number of features and gained some bug fixes...

Here is brief list of changes:

* Renamed from fb2conv to fb2mobi (MyHomeLib integration)
* Ported to Python 3.4.2
* Lost UI and "Send To Kindle" functionality
* All messages and profile descriptions got translated to English
* Fixed all problems I was aware of at the moment (see git log)
* Added ability to apply xslt transformation from external file to fb2 before further processing
* Added xslt extension "katz_tr" to speedup and simplify transformation of direct speech in dialogs

Enjoy!
