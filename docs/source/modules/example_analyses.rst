Example Analyses
================

Submodules
----------

CLI Example
--------------------

.. automodule:: example_analyses.analysis_cli_ex1
    :members:
    :undoc-members:
    :show-inheritance:

Analysis Example
----------------

.. literalinclude:: ../../../examples/analysis_ex1.py
   :linenos:

.. automodule:: example_analyses.analysis_ex1
    :members:
    :undoc-members:
    :show-inheritance:

Example analysis script demonstrating how to programatically load and run already persisted
reduced order models. This example loads two response variables (models) from the small office
random forest reduced order models. The loaded models are then passed through the
swee-temp-test.json analysis definition file. The analysis definition has few fixed
covariates and a few covariates with multiple values to run.

To run this example

.. code-block:: bash

    python analysis_ex1.py

Modelica Example
----------------

.. automodule:: example_analyses.analysis_modelica_ex1
    :members:
    :undoc-members:
    :show-inheritance:
