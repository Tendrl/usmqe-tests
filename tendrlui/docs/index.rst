Tendrl
======

Tendrl is a Python library which is build over `Widgetastic`_ and `navmazing`_
to make Satellite 6 UI testing easier.

Tendrl is written in Python 3 and do not plan to support Python 2. Tendrl
supports Satellite 6.4 and above and Foreman 1.17 and above (with vertical
navigation).

This page provides a summary of information about Tendrl.

.. contents::

More in-depth coverage is provided in other sections.

.. toctree::
    :maxdepth: 1

    build-docs
    api/index
    examples


Concepts
--------

Besides code which implements Widgetastic and navmazing functionality, two
basic concepts used to abstract Satellite/Foreman UI functionality are Views
and Entities.

**View** is fundamental basic concept that describes appearance of the page.
Here we store all information about controls (widgets) on the page,
specifically locators to them or when control is basic one that has common
locator we just define widget without any further details. Of course, we
try to address locators using `id=` or `name=` as first priority, but if we
can't - we go with XPath. If you see situation like this - create Foreman or
Katello pull request to assign unique id attribute for necessary element
where it is reasonable, as XPaths are more fragile and has worse performance
to interact with.

**Entity** is fundamental basic concept that is responsible for functional
side of application (Satellite in our case). It defines actions you can do
with objects like CRUD (create, remove, update, delete) for example. That
is only API that is visible for end user on test side. Also, we put all
details about navigation here, so framework knows how to get to necessary
page when you need to create specific object in the application.

Tendrl adds bunch of **widgets** (which are specific to Satellite / Foreman
web UI) to these defined by Widgetastic (like generic `Text`). Widgets allows
you to interact with various UI elements and are used in views.

And finally tests. Tests are not part of Tendrl repository. You can contribute
tests to the Robottelo, ``tests/foreman/`` `ui_tendrlui`_ folder (see "Quick
start guide" below).


Quick start guide
-----------------

1. Clone Robottelo:

.. code-block:: bash

    git clone https://github.com/SatelliteQE/robottelo.git

2. Install requirements

.. code-block:: bash

    cd robottelo && pip install -r requirements.txt

3. Create `robottelo.properties` file and fill it with your values (your may
reuse already existing properties file since no changes were introduced there)

.. code-block:: bash

    cp robottelo.properties.sample robottelo.properties
    vim robottelo.properties

4. Run tendrlui tests from Robottelo's ``tests/foreman/ui_tendrlui/`` folder

.. code-block:: bash

    pytest tests/foreman/ui_tendrlui/test_architecture.py


Contributing
------------

Good practice when working with Python project as Tendrl is to work in
Python's virtual environments. To initiate and activate them before running
`pip ...` commands run:

.. code-block:: bash

    virtualenv venv   # on Fedora you might need to use `virtualenv-3` if you have Python 2 as a default on your system
    source venv/bin/activate

If you are about to start contributing, please follow `GitHub flow`_.

For a new-comer, we have issues tagged with "`good first issue`_" so that
might be place where you can start?

When testing your Tendrl code using Robottelo tests, you can make sure your
development checkout of Tendrlui is used (instead the one installed in your
Robottelo virtual environment) by setting `PYTHONPATH` properly (you can
add that line at the end of your virtual environment activation script
`venv/bin/activate` so it is set automatically next time you source it):

.. code-block:: bash

    export PYTHONPATH="/home/username/workspace/tendrlui/:$PYTHONPATH"

When you are running your tests locally, you will need Chrome browser
installed and `chromedriver`_ (download and unzip it) binary location
set in `webdriver_binary=` configuration option in your
`robottelo.properties` (or make it available somewhere in your PATH,
e.g. in Robottelo `venv/bin/`).

As of now, `only chromedriver`_ is supported.


.. _Widgetastic: https://github.com/RedHatQE/widgetastic.core
.. _navmazing: https://github.com/RedhatQE/navmazing/
.. _ui_tendrlui: https://github.com/SatelliteQE/robottelo/tree/master/tests/foreman/ui_tendrlui
.. _GitHub flow: https://help.github.com/articles/github-flow/
.. _good first issue: https://github.com/SatelliteQE/tendrlui/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22
.. _chromedriver: https://sites.google.com/a/chromium.org/chromedriver/downloads
.. _only chromedriver: https://github.com/SatelliteQE/tendrlui/issues/1
