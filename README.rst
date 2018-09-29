Reduced Order Modeling Framework
================================

|build| |docs|


The reduced order model (ROM) framework was created to build models to use for estimating
commercial building energy loads. The framework currently supports linear models,
random forests, and support vector regressions. The framework handles the building,
evalulation, and validation of the models. During each set of the process, the framework
exports diagnostic data for the user to evaluate the performance of the reduced
order models. In addition to building, evaluating, and validating the reduced order models, the framework
is able to load previously persisted model to be used in third-party applications (e.g. Modelica).

The project was developed focused on evaluating ambient loop distric heating and cooling systems.
As a result, there are several hard coded methods designed to evaluate and validate building
energy modeling data.

This documention will discuss how to build, evaluate, and validate a simple dataset focused on
commercial building energy consumption. The documentation will also demonstrate how to load and run an already
built ROM to be used to approximate building energy loads.

------------
Instructions
------------

The ROM Framework requires `Python 3 <https://www.python.org/>`_. After installing Python and configuring Python 3,
the ROM Framework can be installed from source code (recommended) or from `PyPI <https://pypi.python.org/pypi>`_.
If you are planning on building, evaluating, and validating custom models, then it is preferred to checkout this
repository from Github. If the use case is to only run prebuilt models, then installing from PyPI is most
likely sufficient.

Installation from Source
========================

1) Install Python and pip
1) Clone this repo
1) Install the Python dependencies

    .. code-block::

        pip install -r requirements.txt

1) (Optional) install graphviz to visualize decision trees

    * OSX: :code:`brew install graphviz`


Building Example Models
=======================

A small office example has been included with the source code. The small office includes 3,300
hourly samples of building energy consumption with several characteristics for each sample. The
example shown here is only the basics, for further instructions view the complete documentation
on `readthedocs <https://reduced-order-modeling-framework.readthedocs.io/en/latest/>`_.

    ./rom-runner build -a smoff_test
    ./rom-runner evaluate -a smoff_test
    ./rom-runner validate -a smoff_test

Installation from PyPI
======================

To be completed.


.. |build| image:: https://travis-ci.org/nllong/ROM-Framework.svg?branch=develop
    :target: https://travis-ci.org/nllong/ROM-Framework

.. |docs| image:: https://readthedocs.org/projects/reduced-order-modeling-framework/badge/?version=latest
    :target: https://reduced-order-modeling-framework.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
