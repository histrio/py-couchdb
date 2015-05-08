.. _install:

Installation
============

This part of the documentation covers the installation of ``py-couchdb``.


Distribute & Pip
----------------

Installing ``py-couchdb`` is simple with `pip <http://www.pip-installer.org/>`_::

    $ pip install pycouchdb


Cheeseshop Mirror
-----------------

If the Cheeseshop is down, you can also install Requests from one of the
mirrors. `Crate.io <http://crate.io>`_ is one of them::

    $ pip install -i http://simple.crate.io/ pycouchdb


Get the Code
------------

``py-couchdb`` is actively developed on GitHub, where the code is
`always available <https://github.com/histrio/py-couchdb>`_.

You can either clone the public repository::

    git clone git://github.com/histrio/py-couchdb.git

Once you have a copy of the source, you can embed it in your Python package,
or install it into your site-packages easily::

    $ python setup.py install
