import pandas as pd
from pyproj import Transformer, CRS

data = {'Stop Name': ['Grange Blanche', 'Parc du Chêne', 'Lycée Jean-Paul Sartre', 'Eurexpo', 'Hotel De Ville - Bron'],
        'Latitude': [45.742938, 45.746139, 45.738028, 45.7284259, 45.733333],
        'Longitude': [4.878842, 4.889491, 4.922213, 4.9602328, 4.916667]}

df = pd.DataFrame(data)

# Define coordinate systems and transformer
lambert_93 = CRS("EPSG:2154")
wgs84 = CRS("EPSG:4326")
transformer_to_lambert = Transformer.from_crs(wgs84, lambert_93)

def convert_to_lambert_str(row):
    lat = row['Latitude']
    lon = row['Longitude']
    x, y = transformer_to_lambert.transform(lat, lon)
    return f"{x} {y}"

df['LAMBERT'] = df.apply(convert_to_lambert_str, axis=1)
print(df)

pd.set_option('display.max_rows', None)  # Display all rows
pd.set_option('display.max_columns', None)  # Display all columns

demand = pd.read_csv('INPUTS/test_demandes.csv', sep=';')
demand = demand.merge(df[['LAMBERT', 'Stop Name']], how='left', left_on='ORIGIN', right_on='LAMBERT')
demand = demand.merge(df[['LAMBERT', 'Stop Name']], how='left', left_on='DESTINATION', right_on='LAMBERT', suffixes=('', ' Dest'))
print(demand[['ID', 'Stop Name', 'Stop Name Dest']])