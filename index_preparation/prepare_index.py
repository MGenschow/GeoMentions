######## Data taken from
# Geonames.org under CC BY 4.0 License
# Download Link for zip archive: https://download.geonames.org/export/dump/allCountries.zip

import pandas as pd
import json
import numpy as np
import gzip


def create_index(level = 'city'):
	"""
	Generate and save an index of geographical data from the Geonames.org dataset.

	This function reads data from 'allCountries.txt', filters and processes the dataset based on the specified
	geographical level ('city' or 'country'). For the 'city' level, it selects records with feature class 'P' and
	feature codes such as 'PPL', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', and 'PPLC', and filters for cities with a population
	greater than 1000. For the 'country' level, it selects records with feature class 'A' and feature code 'PCLI'.
	The function then processes the 'alternatenames' column by splitting comma-separated names into lists, exploding the
	DataFrame, filling missing alternate names with the main name, and sorting to retain the entry with the highest population
	for each alternate name. It removes duplicate keys (alternate names) that are shorter than 3 characters, creates a dictionary
	mapping each alternate name to a dictionary of attributes (name, country_code, population, timezone, and coordinates),
	and finally saves this index as a gzipped JSON file in the '../geomentions/data/' directory.

	Parameters:
	    level (str, optional): The geographical level to index. Must be either 'city' or 'country'. Defaults to 'city'.

	Returns:
	    None

	Side Effects:
	    Writes a gzipped JSON file named '{level}_index.json.gz' to the '../geomentions/data/' directory.
	"""
	columns = [
		"geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude",
		"feature_class", "feature_code", "country_code", "cc2", "admin1_code",
		"admin2_code", "admin3_code", "admin4_code", "population", "elevation",
		"dem", "timezone", "modification_date"
	]
	df = pd.read_csv('allCountries.txt', sep='\t',
					 low_memory=False,
					 names=columns
					)

	# Subset to level
	if level == 'city':
		feature_codes = {"PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"}
		df = df[(df.feature_class == 'P') & (df.feature_code.isin(feature_codes))]
		df = df[df.population > 1000]
		print(f"Shape of dataset for level {level}: {df.shape[0]}")

	elif level == 'country':
		df = df[(df.feature_class == 'A') & (df.feature_code == 'PCLI')]

	# Process the "alternatenames" column: split comma-separated names into lists then explode the dataframe
	df["alternatenames"] = df["alternatenames"].str.split(",")
	df = df.explode("alternatenames").reset_index(drop=True)

	# Replace missing alternatenames with the city's main name
	df['alternatenames'] = df['alternatenames'].fillna(df.name)

	# Sort by alternate name and population (highest population first)
	df.sort_values(['alternatenames', 'population'], ascending=False, inplace=True)

	# Keep only the first occurrence of each alternate name (highest population city)
	df.drop_duplicates(subset='alternatenames', keep='first', inplace=True)

	# Rename the column for consistency
	df.rename(columns={'alternatenames': "key"}, inplace=True)

	# Remove all rows where the key is less than 3 characters long
	df = df[df.key.notna()]
	df = df[df.key.apply(len) > 2]

	# Convert the DataFrame into a dictionary indexed by city name (including alternatenames)
	df['coordinates'] = list(zip(df.latitude, df.longitude))
	cols = ['key', 'name', 'country_code', 'population', 'timezone', 'coordinates']
	index = {row.key: {col: row[col] for col in cols if col != 'key'} for row in df[cols].to_records(index=False)}

	# Save the index as a JSON file
	#with open(f"data/{level}_index.json", "w") as fp:
	#	json.dump(index, fp, default=lambda x: int(x) if isinstance(x, np.integer) else x)

	with gzip.open(f"../geomentions/data/{level}_index.json.gz", "wt", encoding="utf-8") as fp:
		json.dump(index, fp, default=lambda x: int(x) if isinstance(x, np.integer) else x)


create_index('city')
create_index('country')



