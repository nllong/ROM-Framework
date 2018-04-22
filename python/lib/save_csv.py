import pandas as pd

def save_multidimensional_csvs(data, rom, analysis, analysis_id, first_dimension_var):
    """
    pull apart the dataframe to create multiple csv files
    We want a CSV for each response for each mass flow rate
    Data in the CSV is datetime on y, ets inlet temp on X

    :return:
    """
    for index, rs in enumerate(rom.response_names):
        print "Creating CSV for %s" % rs

        for unique_value in data[first_dimension_var].unique():
            file_name = 'output/%s/lookup_tables/%s_%s_mass_flow_%s.csv' % (analysis_id, analysis.lookup_prepend, rs, unique_value)
            lookup_df = data[data[first_dimension_var] == unique_value]

            # Save the data times in a new dataframe (will be in order)
            save_df = pd.DataFrame.from_dict({'datetime': lookup_df['datetime'].unique()})
            for unique_value_2 in data['ETSInletTemperature'].unique():
                new_df = lookup_df[lookup_df['ETSInletTemperature'] == unique_value_2]
                save_df[unique_value_2] = new_df[rs].values

            save_df.to_csv(file_name, index=False)
