# Ambient Loop Reduced Order Models

[![Build Status](https://travis-ci.org/nllong/ambient-loop-analysis.svg?branch=develop)](https://travis-ci.org/nllong/ambient-loop-analysis)

## Instructions

The Ambient Loop Reduced Order Models are written in Python and primarily use the RandomForest
library from the scikit-learn packages. The models are generated by running a reasonable number
of EnergyPlus simulations using OpenStudio and OpenStudio Server to create a large enough parameter
space for the Random Forest Regressor to reasonable train the models.

Follow the instructions below to use the models:

1) Clone this repo
1) Set your directory to the python directory. `cd python`
1) Install Python and Pip
1) Determine which models to use, with or without mass flow rate and download the models from the 
links below.

    Latest Models (recommended):
    * [Without Mass Flow Rate](https://s3.amazonaws.com/openstudio-metamodels/small_office/latest/3ff422c2-ca11-44db-b955-b39a47b011e7/models/models.zip)
    * [With Mass Flow Rate](https://s3.amazonaws.com/openstudio-metamodels/small_office/latest/66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e/models/models.zip)

    Last Release
    * [Without Mass Flow Rate](https://s3.amazonaws.com/openstudio-metamodels/small_office/release/3ff422c2-ca11-44db-b955-b39a47b011e7/models/models.zip)
    * [With Mass Flow Rate](https://s3.amazonaws.com/openstudio-metamodels/small_office/release/66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e/models/models.zip)

1) Place the models in the ./output/<analysis_id>/models directory. The analysis_id will be one of the
following:
        
    Without Mass Flow Rate -- 3ff422c2-ca11-44db-b955-b39a47b011e7
    With Mass Flow Rate -- 66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e     

1) Install the Python dependencies

    ```bash
    pip install -r requirements.txt
    ``` 
    
1) Run the model

    ```bash
    python smoffice.py --help
    ``` 
    
    Without Mass Flow
    
    ```bash
    python smoffice.py -a 3ff422c2-ca11-44db-b955-b39a47b011e7
    ```
    
    With Mass Flow 
    
    ```bash
    python smoffice.py -a 66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e
    ```
    
    There are many arguments that are passed to the command line. To see the parameters run
    `python smoffice.py --help`.
