.. ixcom documentation master file, created by
   sphinx-quickstart on Wed Aug  7 10:23:35 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ixcom: Communication with iMAR devices
======================================

The ixcom python package makes communication with iMAR's inertial navigation systems speaking
the iXCOM protocol very simple.

Installation
------------

The ixcom package can be installed from pypi.org:

.. code-block:: bash

    pip install ixcom

Examples
--------

Connect to the system with IP 192.168.1.30 and start a new alignment:

.. code-block:: python

    import ixcom

    client = ixcom.Client('192.168.1.30')
    client.open_last_free_channel()
    client.realign()


Contact
-------

For questions going beyond this documentation or about the iMAR navigation systems,
please contact support@imar-navigation.de .

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: API documentation

   ixcom
   protocol

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Examples

   examples

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Command line utilities

   cli





