Using the ROMs
==============

CLI Example
-----------

.. literalinclude:: ../../../examples/analysis_cli_ex1.py
   :linenos:

Analysis Example
----------------

Example analysis script demonstrating how to programatically load and run already persisted
reduced order models. This example loads two response variables (models) from the small office
random forest reduced order models. The loaded models are then passed through the
swee-temp-test.json analysis definition file. The analysis definition has few fixed
covariates and a few covariates with multiple values to run.

To run this example

.. code-block:: bash

    python analysis_ex1.py


.. literalinclude:: ../../../examples/analysis_ex1.py
   :linenos:

Sweep Example
-------------

.. literalinclude:: ../../../examples/analysis_sweep_ex1.py
   :linenos:

Modelica Example
----------------

.. literalinclude:: ../../../examples/analysis_modelica_ex1.py
   :linenos:
