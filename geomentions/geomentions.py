import json
from collections import Counter, namedtuple
import regex
from typing import List, Tuple, Optional
import gzip
import os
import unicodedata


def get_data_path(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', path)

class GeoResult:
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
    def __init__(self, city_mentions: List[CityMention], country_mentions: List[CityMention]):
        self.city_mentions = city_mentions
        self.country_mentions = country_mentions

    def __repr__(self):
        return f"GeoMentionsResult(cities={sum([elem.count for elem in self.city_mentions])}, countries={sum([elem.count for elem in self.country_mentions])})"

    def to_dict(self):
        return {
            "city_mentions": [city._asdict() for city in self.city_mentions],
            "country_mentions": [country._asdict() for country in self.country_mentions],
        }

    def filter_cities(self, min_population: Optional[int] = None, max_population: Optional[int] = None,
                      country_code: Optional[str] = None):
        return [
            city for city in self.city_mentions
            if (min_population is None or city.population >= min_population)
               and (max_population is None or city.population <= max_population)
               and (country_code is None or city.country_code == country_code)
        ]

    @property
    def country_counts(self):
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
    def __init__(self, standardize_names=True):
        self.standardize_names = standardize_names
        with gzip.open(get_data_path("city_index.json.gz"), "rt", encoding="utf-8") as fp:
            self.city_index = json.load(fp)
        with gzip.open(get_data_path("country_index.json.gz"), "rt", encoding="utf-8") as fp:
            self.country_index = json.load(fp)

    def _split_text(self, text: str) -> List[str]:
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
        return [(word_list[i], word_list[i + 1]) for i in range(len(word_list) - 1)]

    def _find_mentions(self, sample: str, level: str) -> List[GeoResult]:
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
        city_collection = self._find_mentions(text, level='city')
        country_collection = self._find_mentions(text, level='country')

        city_mentions = self.count_results(city_collection, self.standardize_names)
        country_mentions = self.count_results(country_collection, self.standardize_names)

        return GeoMentionsResult(city_mentions, country_mentions)
