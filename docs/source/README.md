

## Installation

```bash
pip install geomentions
```

## Usage

Below is a quick example of how to use geomentions:

```python
from geomentions import GeoMentions

# Instantiate the GeoMentions (True (default) means we standardize names to a single variant (Munich and München is counted as the same entity))
gt = GeoMentions(standardize_names=True)

text = "Munich is in Germany can be translated to german as München ist in Deutschland. Another city that is mentioned here is New York."
result = gt.fit(text)

# Basic summary
print(result)
# GeoMentionsResult(cities=3, countries=2)
# This counts all city and country mentions, also duplicates

# City mentions
print(result.city_mentions)
# [CityMention(name='Munich', count=2, country_code='DE', population=1260391, coordinates=[48.13743, 11.57549]),
# CityMention(name='New York City', count=1, country_code='US', population=8804190, coordinates=[40.71427, -74.00597])]

# Country mentions
print(result.country_mentions)
# [CityMention(name='Federal Republic of Germany', count=2, country_code='DE', population=82927922, coordinates=[51.5, 10.5])]

# All country counts (implicit and explicit mentions):
print(result.country_counts)
# {'DE': {'total_count': 4, 'implicit_count': 2, 'explicit_count': 2},
# 'US': {'total_count': 1, 'implicit_count': 1, 'explicit_count': 0}}

# Filter city results by country code
print(result.filter_cities(country_code='US'))
# [CityMention(name='New York City', count=1, country_code='US', population=8804190, coordinates=[40.71427, -74.00597])]

# Filter city mentions by minimum population
print(result.filter_cities(min_population=3_000_000))
# [CityMention(name='New York City', count=1, country_code='US', population=8804190, coordinates=[40.71427, -74.00597])]

# Filter city mentions by max population
print(result.filter_cities(max_population=3_000_000))
# [CityMention(name='Munich', count=2, country_code='DE', population=1260391, coordinates=[48.13743, 11.57549])]

# Extract data fields from a matched entity
print(result.city_mentions[0].coordinates)
#  [48.13743, 11.57549]

# Convert result to a dictionary
print(result.to_dict())
```

## Features

- **City & Country Detection**: Identify city and country mentions in text (including bigrams).
- **Population & Coordinates**: Retrieve population, country code, coordinates, and time zone for mentioned entities.
- **Summaries by Country**: Automatically count how many times a city or country is mentioned.
- **Filtering**: Filter mentions by minimum population or country code.
- **Multi-Language**: City and country entities are detected in many languages and almost all spellings.
- **Lightweight and fast**: No external dependencies

## Language Support

- The package supports all languages given in the GeoNames database
- In the `alternate names` table GeoNames supports ~600 languages. In this implementation the support might be slightly lower but still in the hundreds.

```python
from geomentions import GeoMentions

gt = GeoMentions(standardize_names=True)

text = "Берлин is the cyrillic spelling for Berlin"
print(gt.fit(text).city_mentions)
# [CityMention(name='Berlin', count=2, country_code='DE', population=3426354, coordinates=[52.52437, 13.41053])]

text = "கம்பளை is the spelling for the city Gampola in Sri Lanka"
print(gt.fit(text).city_mentions)
# [CityMention(name='Gampola', count=2, country_code='LK', population=24283, coordinates=[7.1643, 80.5696]),
# CityMention(name='Lanka', count=1, country_code='IN', population=36805, coordinates=[25.92907, 92.94856])]

text = "'자르브뤼켄 is the spelling for Saarbrücken in Germany"
print(gt.fit(text).city_mentions)
# [CityMention(name='Saarbrücken', count=2, country_code='DE', population=179349, coordinates=[49.23262, 7.00982])]


```

## Underlying Data

- **Source**: [GeoNames.org](https://www.geonames.org) database
- **License**: Creative Commons Attribution 4.0 License
- **Index creation**: Data is preprocessed to make the package lightweight and fast. The index creation script can be accessed [here](https://github.com/MGenschow/GeoMentions/blob/main/index_preparation/prepare_index.py).

#### City Index:

- All cities from the GeoNames database with >1000 inhabitants
- 107.444 unique cities supported
- 671.784 entries in index (multiple spellings and languages per unique city)

#### City Index:

- All countries from the GeoNames database
- 193 unique cities supported
- 32.010 entries in index (multiple spellings and languages per unique country)

#### Access the index

```python 
from geomentions import GeoMentions

gt = GeoMentions()
city_index = gt.city_index
county_index = gt.country_index
```


## Contributing

Contributions to GeoMentions are highly welcome! If you want to contribute, either: 

- **Report Issues:**  
   - If you find a bug or have a suggestion, please open an issue in the GitHub [issue tracker](https://github.com/MGenschow/GeoMentions/issues).

or 

- **Implement features/bugfixes yourself:**

   1. **Fork & Branch:**  
   Fork the repository and create a new branch for your changes (e.g., `feature/new-feature` or `bugfix/issue-number`).
   
   2. **Make Changes & Test:**  
   Implement your improvements. If applicable, add tests to cover your changes and update documentation as needed. Make sure all the test in `tests/test_geomentions.py` pass.
   
   3. **Submit a Pull Request:**  
   Push your branch to your fork and open a pull request against the main repository. Provide a brief description of your changes.

Thank you for helping to improve GeoMentions!

## Changelog

### [0.0.1] - 2025-02-23
- Initial release.

## License
MIT License

Copyright (c) 2025 Malte Genschow

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
