import pytest
from geomentions import GeoMentions, GeoMentionsResult, CityMention, GeoResult


def test_georesult_initialization_valid_data():
    entry = {
        'name': "Munich",
        'country_code': "DE",
        'population': 1500000,
        'timezone': "CET",
        'coordinates': "48.1351,11.5820"
    }
    geo_result = GeoResult(name="Munich", entry=entry)

    assert geo_result.name == "Munich"
    assert geo_result.country_code == "DE"
    assert geo_result.population == 1500000
    assert geo_result.time_zone == "CET"
    assert geo_result.coordinates == "48.1351,11.5820"


def test_georesult_initialization_missing_data():
    entry = {
        'name': "Munich",
        'country_code': "DE",
        'population': 1500000,
        'timezone': "CET"
    }
    geo_result = GeoResult(name="Munich", entry=entry)

    assert geo_result.coordinates is None  # Default value is None if not present


def test_geomentions_split_text_valid():
    text = "München ist in Deutschland, Munich is in Germany"
    gt = GeoMentions()
    result = gt._split_text(text)

    expected = ["München", "ist", "in", "Deutschland", "Munich", "is", "in", "Germany"]
    assert result == expected


def test_geomentions_split_text_empty():
    text = ""
    gt = GeoMentions()
    result = gt._split_text(text)

    assert result == []


def test_geomentions_split_text_with_special_characters():
    gt = GeoMentions()

    text = "München's airport is in Germany."
    result = gt._split_text(text)
    expected = ["München", "airport", "is", "in", "Germany"]
    assert result == expected

    text = "Las-Vegas is written incorrectly"
    result = gt._split_text(text)
    expected = ["Las", "Vegas", "is", "written", "incorrectly"]
    assert result == expected

    text = "St.-Martin might be a city"
    result = gt._split_text(text)
    expected = ["St", "Martin", "might", "be", "a", "city"]
    assert result == expected


def test_geomentions_generate_bigrams_valid():
    words = ["München", "ist", "in", "Deutschland"]
    gt = GeoMentions()
    result = gt._generate_bigrams(words)

    expected = [("München", "ist"), ("ist", "in"), ("in", "Deutschland")]
    assert result == expected


def test_geomentions_generate_bigrams_empty():
    words = []
    gt = GeoMentions()
    result = gt._generate_bigrams(words)

    assert result == []


def test_geomentions_generate_bigrams_single_word():
    words = ["München"]
    gt = GeoMentions()
    result = gt._generate_bigrams(words)

    assert result == []


def test_geomentions_find_mentions_city():
    entry = {
        'name': "Munich",
        'country_code': "DE",
        'population': 1500000,
        'timezone': "CET",
        'coordinates': "48.1351,11.5820"
    }
    # Mocked index for testing
    gt = GeoMentions()
    gt.city_index = {"Munich": entry}

    result = gt._find_mentions("I visited Munich last year", level="city")

    assert len(result) == 1
    assert result[0].name == "Munich"
    assert result[0].country_code == "DE"
    assert result[0].population == 1500000
    assert result[0].coordinates == "48.1351,11.5820"


def test_geomentions_find_mentions_city_not_found():
    entry = {
        'name': "Munich",
        'country_code': "DE",
        'population': 1500000,
        'timezone': "CET",
        'coordinates': "48.1351,11.5820"
    }
    # Mocked index for testing
    gt = GeoMentions()
    gt.city_index = {"Munich": entry}

    result = gt._find_mentions("I visited Berlin", level="city")

    assert len(result) == 0


def test_geomentions_count_results():
    entry = {
        'name': "Munich",
        'country_code': "DE",
        'population': 1500000,
        'timezone': "CET",
        'coordinates': "48.1351,11.5820"
    }
    # Create a list of GeoResult instances for testing
    geo_results = [GeoResult(name="Munich", entry=entry)] * 5  # 5 mentions of Munich

    gt = GeoMentions()
    result = gt.count_results(geo_results, standardize_names=True)

    assert len(result) == 1
    assert result[0].name == "Munich"
    assert result[0].count == 5
    assert result[0].country_code == "DE"


def test_geomentions_fit_valid():
    text = "München ist in Deutschland, Munich is in Germany"
    gt = GeoMentions()
    result = gt.fit(text)

    assert isinstance(result, GeoMentionsResult)
    assert len(result.city_mentions) == 1
    expected = [CityMention(name='Munich', count=2, country_code='DE', population=1260391, coordinates=[48.13743, 11.57549])]
    assert result.city_mentions == expected
    expected = [CityMention(name='Federal Republic of Germany', count=2, country_code='DE', population=82927922, coordinates=[51.5, 10.5])]
    assert result.country_mentions == expected


def test_geomentions_fit_valid_non_standardization():
    text = "München ist in Deutschland, Munich is in Germany"
    gt = GeoMentions(standardize_names=False)
    result = gt.fit(text)

    assert isinstance(result, GeoMentionsResult)
    assert len(result.city_mentions) == 2
    expected = [CityMention(name='München', count=1, country_code='DE', population=1260391, coordinates=[48.13743, 11.57549]),
                CityMention(name='Munich', count=1, country_code='DE', population=1260391, coordinates=[48.13743, 11.57549])]
    assert result.city_mentions == expected
    assert len(result.country_mentions) == 2
    expected = [CityMention(name='Deutschland', count=1, country_code='DE', population=82927922, coordinates=[51.5, 10.5]),
                CityMention(name='Germany', count=1, country_code='DE', population=82927922, coordinates=[51.5, 10.5])]
    assert result.country_mentions == expected

def test_geomentions_fit_empty_text():
    text = ""
    gt = GeoMentions()
    result = gt.fit(text)

    assert isinstance(result, GeoMentionsResult)
    assert len(result.city_mentions) == 0
    assert len(result.country_mentions) == 0


def test_geomentions_fit_with_single_city():
    text = "I went to Munich."
    gt = GeoMentions()
    result = gt.fit(text)

    assert len(result.city_mentions) == 1
    assert "Munich" in [city.name for city in result.city_mentions]


def test_geomentions_result_filter_cities_by_population():
    city_mentions = [
        CityMention(name="Munich", count=5, country_code="DE", population=1500000, coordinates="48.1351,11.5820"),
        CityMention(name="Berlin", count=3, country_code="DE", population=3500000, coordinates="52.52,13.405")
    ]
    country_mentions = []
    geo_result = GeoMentionsResult(city_mentions, country_mentions)

    filtered_cities = geo_result.filter_cities(min_population=2000000)
    assert len(filtered_cities) == 1
    assert filtered_cities[0].name == "Berlin"


def test_geomentions_result_filter_cities_by_country_code():
    city_mentions = [
        CityMention(name="Munich", count=5, country_code="DE", population=1500000, coordinates="48.1351,11.5820"),
        CityMention(name="Paris", count=2, country_code="FR", population=2200000, coordinates="48.8566,2.3522")
    ]
    country_mentions = []
    geo_result = GeoMentionsResult(city_mentions, country_mentions)

    filtered_cities = geo_result.filter_cities(country_code="DE")
    assert len(filtered_cities) == 1
    assert filtered_cities[0].name == "Munich"


def test_geomentions_result_country_counts():
    city_mentions = [
        CityMention(name="Munich", count=5, country_code="DE", population=1500000, coordinates="48.1351,11.5820"),
        CityMention(name="Berlin", count=3, country_code="DE", population=3500000, coordinates="52.52,13.405")
    ]
    country_mentions = [
        CityMention(name="Germany", count=1, country_code="DE", population=83000000, coordinates="51.1657,10.4515")
    ]
    geo_result = GeoMentionsResult(city_mentions, country_mentions)

    country_counts = geo_result.country_counts
    assert country_counts["DE"]["total_count"] == 9
    assert country_counts["DE"]["implicit_count"] == 8
    assert country_counts["DE"]["explicit_count"] == 1
