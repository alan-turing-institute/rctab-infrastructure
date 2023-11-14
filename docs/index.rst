Welcome to the RCTab Infrastructure documentation!
==================================================

This is the automated deployment part of RCTab.
If you need them, you can find the full RCTab docs `here <https://rctab.readthedocs.io/>`_.

RCTab can be deployed manually (e.g. via the Azure CLI or portal.azure.com).
However, automated deployment is more convenient, secure and repeatable.
Automated deployment is done with `Pulumi <https://www.pulumi.com/>`_, an Infrastructure as Code tool.
Deployment instructions can be found in :doc:`Deployment <content/deployment>`.

.. toctree::
   :maxdepth: 2
   :caption: External Links
   :glob:
   :hidden:

   RCTab docs home <https://rctab.readthedocs.io/en/latest/>

.. toctree::
   :maxdepth: 2
   :caption: Contents
   :glob:
   :hidden:

   Home <self>
   content/*

.. autosummary::
   :toctree: _autosummary
   :recursive:
   :caption: Docstrings

   rctab_infrastructure

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
