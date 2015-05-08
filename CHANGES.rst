=========
Changelog
=========

Version 1.12
------------

Date: 2015-03-02

- Backward incompatibility: `all` method changes its semantics, the wrapper now
  receives a complete result item and it is the responsibility of wrapper
  to handle it. (thanks to @krisb78)
- Bug fix in __contains__ method of Database class (thanks to @beezz)
- Improved performance on changes_feed (thanks to @krisb78)


Version 1.11
------------

Date: 2015-02-05

- Remove default "since" parameter from `changes_feed` method. (by @krisb78)


Version 1.10
------------

Date: 2015-01-29

- Proper handling heartbeats on changes feed (by @krisb78)
- Add batch option to save method (by @kravietz)
- Fix unicode related problems on python 2.7 (by @bmihelac)


Version 1.9
-----------

Date: 2014-08-23

- Add support for `include_docs='false'`

Version 1.8
-----------

Date: 2014-07-17

- Fix revisions api (Thanks to @GuoJing)
- Speed up JSON decoding (by David Kendal)


Version 1.7
-----------

Date: 2013-12-13

- Fix encoding problems on retrieve data (thanks to Jonas Hagen)

Version 1.6
-----------

Date: 2013-06-29

- Fixed some wrong behavior with use of a simple copy instead of deepcopy.
- Change some default parameters from mutable objects to more pythoninc
  way using immutable types.
  http://pythonconquerstheuniverse.wordpress.com/category/python-gotchas/
- Fixed wrong usage of get_attachmen (now uses properly a rev parameter)


Version 1.5
-----------

Date: 2013-06-16

- Improved error management.
- Improved exception hierarchy.
- Fix a lot of inconsistents on method calls.
- Add a simple way to obtain attachment as stream instead of
  load all content in memory.
- Add a simple way to subscribe to couchdb changes stream.

Thanks to:

- Kristoffer Berdal (@flexd) for hard work on error management improvement.
- @Dedalus2000 for test and report a lot of issues and some ideas.


Version 1.4
-----------

Date: 2013-05-11

- Fixed invalid url parsing on use session (thanks to KodjoSuprem)
- Fixed invalid encode method call (thanks to Kristoffer Berdal)
- Switch to basic auth method as default auth method.
- Add new method "one" for more clean way to obtain a first value
    for a query a view (thanks to Kristoffer Berdal for the initial idea)
- Add flat and as_list parameters to query, one and all methods.


Version 1.3
-----------

Date: 2013-04-04

- Added replication methods thanks to Bruno Bord (@brunobord)


Version 1.2
-----------

Date: 2013-01-27

- All methods that can receive document, do not modify id (inmutable api?)
- Add delete_bulk methods.
- A lot of fixes and improvements on tests.


Version 1.1
-----------

Date: 2013-01-27

- Add python view server (imported from https://github.com/lilydjwg/couchdb-python3 with some changes).
- Now compatible with pypy.


Version 1.0
-----------

- Initial version.
