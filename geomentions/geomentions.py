import json
from collections import Counter, namedtuple
import regex
from typing import List, Tuple, Optional
import gzip
import os
import unicodedata


def get_data_path(path):
    """
    Return the absolute path to a file in the 'data' directory relative to the current file.

    Parameters:
        path (str): Relative file path within the 'data' directory.

    Returns:
        str: Absolute path to the specified file.
    """
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', path)

class GeoResult:
    """
    Represents a geographical location result with associated metadata.

    Attributes:
        key (str): The identifier or key for the location.
        name (str): The name of the location.
        country_code (str): The country code associated with the location.
        population (int): The population of the location.
        time_zone (str): The time zone of the location.
        coordinates (str): The geographical coordinates of the location.
    """
    def __init__(self, name, entry):
        self.key: str = name
        self.name: str = entry.get('name')
        self.country_code: str = entry.get('country_code')
        self.population: int = entry.get('population')
        self.time_zone: str = entry.get('timezone')
        self.coordinates: str = entry.get("coordinates")

    def __repr__(self):
        return (
            f"GeoResult(key={self.key!r}, name={self.name!r}, "
            f"country={self.country_code})"
        )

CityMention = namedtuple("CityMention", ["name", "count", "country_code", "population", "coordinates"])

class GeoMentionsResult:
    """
    Holds the results of geographical mentions, including lists of city and country mentions.

    Attributes:
        city_mentions (List[CityMention]): A list of city mention records.
        country_mentions (List[CityMention]): A list of country mention records.
    """
    def __init__(self, city_mentions: List[CityMention], country_mentions: List[CityMention]):
        self.city_mentions = city_mentions
        self.country_mentions = country_mentions

    def __repr__(self):
        return f"GeoMentionsResult(cities={sum([elem.count for elem in self.city_mentions])}, countries={sum([elem.count for elem in self.country_mentions])})"

    def to_dict(self):
        """
        Convert the GeoMentionsResult instance to a dictionary.

        Returns:
            dict: A dictionary with keys 'city_mentions' and 'country_mentions', each mapping to
                  a list of dictionaries representing the respective mention records.
        """
        return {
            "city_mentions": [city._asdict() for city in self.city_mentions],
            "country_mentions": [country._asdict() for country in self.country_mentions],
        }

    def filter_cities(self, min_population: Optional[int] = None, max_population: Optional[int] = None,
                      country_code: Optional[str] = None):
        """
        Filter city mentions based on population thresholds and country code.

        Parameters:
            min_population (Optional[int]): Minimum population required (inclusive). Defaults to None.
            max_population (Optional[int]): Maximum population allowed (inclusive). Defaults to None.
            country_code (Optional[str]): Specific country code to filter by. Defaults to None.

        Returns:
        List[CityMention]: A list of city mentions that satisfy the given criteria.
        """
        return [
            city for city in self.city_mentions
            if (min_population is None or city.population >= min_population)
               and (max_population is None or city.population <= max_population)
               and (country_code is None or city.country_code == country_code)
        ]

    @property
    def country_counts(self):
        """
        Aggregate mention counts by country, separating implicit and explicit counts.

        Returns:
            dict: A dictionary where each key is a country code and each value is a dictionary containing:
                  - total_count: Combined count from city and country mentions.
                  - implicit_count: Count from city mentions only.
                  - explicit_count: Count from country mentions only.
        """
        country_counter = Counter()
        implicit_counter = Counter()
        explicit_counter = Counter()

        for city in self.city_mentions:
            if city.country_code:
                country_counter[city.country_code] += city.count
                implicit_counter[city.country_code] += city.count

        for country in self.country_mentions:
            country_counter[country.country_code] += country.count
            explicit_counter[country.country_code] += country.count

        return {
            country: {
                "total_count": country_counter[country],
                "implicit_count": implicit_counter[country],
                "explicit_count": explicit_counter[country]
            }
            for country in country_counter
        }

class GeoMentions:
    """
    Processes text to identify and count geographical mentions using preloaded city and country indices.
    """
    def __init__(self, standardize_names=True):
        self.standardize_names = standardize_names
        with gzip.open(get_data_path("city_index.json.gz"), "rt", encoding="utf-8") as fp:
            self.city_index = json.load(fp)
        with gzip.open(get_data_path("country_index.json.gz"), "rt", encoding="utf-8") as fp:
            self.country_index = json.load(fp)

    def _split_text(self, text: str) -> List[str]:
        """
        Normalize the input text and split it into a list of words.

        The method normalizes Unicode text to NFKC, removes specific possessive patterns, replaces non-alphanumeric
        characters (except for letters, marks, numbers, and whitespace) with spaces, and then splits the text by whitespace.

        Parameters:
            text (str): The input text to process.

        Returns:
            List[str]: A list of processed words extracted from the text.
        """
        # Normalize Unicode text to NFKC form for consistent representation.
        text = unicodedata.normalize('NFKC', text)

        text = regex.sub(r"(?<=\p{L})'[\p{L}\p{M}]*", '', text)

        # Replace any character that is NOT:
        # - a Unicode letter (\p{L})
        # - a Unicode combining mark (\p{M})
        # - a Unicode number (\p{N})
        # - whitespace (\s)
        # with a space. This preserves full characters in scripts like Tamil or other languages.
        text = regex.sub(r"[^\p{L}\p{M}\p{N}\s]", " ", text)

        # Split the text into words based on whitespace.
        return text.split()

    def _generate_bigrams(self, word_list: List[str]) -> List[Tuple[str, str]]:
        """
        Generate bigrams from a list of words.

        Parameters:
            word_list (List[str]): A list of words.

        Returns:
            List[Tuple[str, str]]: A list of tuples where each tuple consists of two consecutive words.
        """

        return [(word_list[i], word_list[i + 1]) for i in range(len(word_list) - 1)]

    def _find_mentions(self, sample: str, level: str) -> List[GeoResult]:
        """
        Identify geographical mentions in the provided text sample based on the specified level.

        Parameters:
            sample (str): The text in which to search for geographical mentions.
            level (str): The level of mention to search for; should be either 'city' or 'country'.

        Returns:
            List[GeoResult]: A list of GeoResult objects representing the detected geographical mentions.
        """
        collection = []
        index = self.city_index if level == 'city' else self.country_index
        words = self._split_text(sample)
        matched_words = set()

        if len(words) == 1:
            entry = index.get(words[0])
            if entry is not None:
                collection.append(GeoResult(words[0], entry))
        else:
            for bigram in self._generate_bigrams(words):
                bigram_lookup = " ".join(bigram)
                entry = index.get(bigram_lookup)
                if entry is not None:
                    collection.append(GeoResult(bigram_lookup, entry))
                    matched_words.update(bigram)

            for word in words:
                if word in matched_words:
                    continue
                entry = index.get(word)
                if entry:
                    collection.append(GeoResult(word, entry))

        return collection

    def count_results(self, collection: List[GeoResult], standardize_names: bool) -> List[CityMention]:
        """
        Aggregate and count occurrences of geographical mentions from a collection of GeoResult objects.

        Parameters:
            collection (List[GeoResult]): The list of geographical results to count.
            standardize_names (bool): If True, counts are aggregated based on the standardized name; otherwise, based on the key.

        Returns:
            List[CityMention]: A sorted list of CityMention records ordered by descending count.
        """
        key_fn = lambda result: result.name if standardize_names else result.key
        counts = Counter(key_fn(city) for city in collection)
        results = [
            CityMention(
                name=key,
                count=counts[key],
                country_code=city.country_code,
                population=city.population,
                coordinates=city.coordinates,
            )
            for key, city in {key_fn(city): city for city in collection}.items()
        ]
        return sorted(results, key=lambda x: x.count, reverse=True)

    def fit(self, text: str) -> GeoMentionsResult:
        """
        Process the input text to extract and aggregate geographical mentions for both cities and countries.

        Parameters:
            text (str): The text to analyze for geographical mentions.

        Returns:
            GeoMentionsResult: An object containing the aggregated results for city and country mentions.
        """
        city_collection = self._find_mentions(text, level='city')
        country_collection = self._find_mentions(text, level='country')

        city_mentions = self.count_results(city_collection, self.standardize_names)
        country_mentions = self.count_results(country_collection, self.standardize_names)

        return GeoMentionsResult(city_mentions, country_mentions)
