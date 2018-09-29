Analysis Definition
===================

.. toctree::
   :maxdepth: 1

   analysis_definition_ex_single


The analysis definition module is used for loading an already generated reduced order and
running a subsequent analysis. The input is a JSON file that defines each of the
covariates of interest. The analysis can take of

* Single value analysis, see :doc:`example <analysis_definition_ex_single>`

* Sweep values over a year (as defined by an EPW file)

* Sweep values over specified ranges

To run an analysis with a JSON file, first load a metamodel, then load the analysis defintion.

.. code-block:: python

    from rom.analysis_definition.analysis_definition import AnalysisDefinition
    from rom.metamodels import Metamodels

Analysis Definition
-------------------

.. automodule:: rom.analysis_definition.analysis_definition
    :members:
    :undoc-members:
    :show-inheritance:

EPW File
--------

.. automodule:: rom.analysis_definition.epw_file
    :members:
    :undoc-members:
    :show-inheritance:
