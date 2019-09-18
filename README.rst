Reduced Order Modeling Framework
================================

|build| |docs|


The reduced order model (ROM) framework was created to build models to use for estimating commercial building energy loads. The framework currently supports linear models, random forests, and support vector regressions. The framework handles the building, evalulation, and validation of the models. During each set of the process, the framework exports diagnostic data for the user to evaluate the performance of the reduced order models. In addition to building, evaluating, and validating the reduced order models, the framework is able to load previously persisted model to be used in third-party applications (e.g. Modelica).

The project was developed focusing on evaluating ambient loop district heating and cooling systems. As a result, there are several hard coded methods designed to evaluate and validate building energy modeling data.

This documentation will discuss how to build, evaluate, and validate a simple dataset focused on commercial building energy consumption. The documentation will also demonstrate how to load and run an already built ROM to be used to approximate building energy loads.

------------
Instructions
------------

The ROM Framework requires `Python 3 <https://www.python.org/>`_. After installing Python and configuring Python 3, the ROM Framework can be installed from source code (recommended) or from `PyPI <https://pypi.python.org/pypi>`_.

Installation from Source
========================

1) Install Python and pip

2) Clone this repository

3) Install the Python dependencies

    .. code-block:: sql
        :linenos:

        pip install -r requirements.txt

4) (Optional) install graphviz to visualize decision trees

    * OSX: :code:`brew install graphviz`


Building Example Models
=======================

A small office example has been included with the source code under the rom/tests directory. The small office includes 3,300 hourly samples of building energy consumption with several characteristics for each sample. The example shown here is only the basics, for further instructions view the complete documentation on `readthedocs <https://reduced-order-modeling-framework.readthedocs.io/en/develop/>`_.

    .. code-block:: bash
        :linenos:

        ./rom-runner build -f rom/tests/smoff_test/metamodels.json -a smoff_test
        ./rom-runner evaluate -f rom/tests/smoff_test/metamodels.json -a smoff_test
        ./rom-runner validate -f rom/tests/smoff_test/metamodels.json -a smoff_test

Installation from PyPI
======================

Not yet complete.

To Dos
======

* Configure better CLI
* Allow for CLI to save results in specific location
* Remove downloaded simulation data from repository
* Write test for running the analysis_definition (currently untested!)

.. |build| image:: https://travis-ci.org/nllong/ROM-Framework.svg?branch=develop
    :target: https://travis-ci.org/nllong/ROM-Framework

.. |docs| image:: https://readthedocs.org/projects/reduced-order-modeling-framework/badge/?version=latest
    :target: https://reduced-order-modeling-framework.readthedocs.io/en/develop/?badge=develop
    :alt: Documentation Status
