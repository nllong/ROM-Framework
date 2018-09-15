import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

df = pd.read_csv('output.csv')
df['datetime'] = df['datetime'].astype('datetime64[m]')
df['DayOfYear'] = df['datetime'].dt.dayofyear

output_dir = 'example_analyses/example_output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

responses = [
    'Modeled RF HeatingElectricity',
    'Modeled RF CoolingElectricity',
    'Modeled RF DistrictCoolingChilledWaterEnergy',
    'Modeled RF DistrictHeatingHotWaterEnergy',
    'Modeled RF ETSHeatingOutletTemperature'
]
for response in responses:
    heatdata = df[["DayOfYear", "Hour", response]].pivot("DayOfYear", "Hour", response)
    f, ax = plt.subplots(figsize=(5, 12))
    sns.heatmap(heatdata)
    plt.savefig('%s/%s.png' % (output_dir,response))
    plt.close('all')
