import os
import pytest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
from listing_getter import ListingGetter

@pytest.fixture
def sample_html(tmp_path):
    # Read the source HTML file
    source_path = Path(os.getenv("WORKDIR"), "tests", "data", "sample.html")
    with source_path.open() as f:
        html_content = f.read()
    
    # Create a temporary test file with the content
    test_file = tmp_path / "test.html"
    test_file.write_text(html_content)
    return f"file://{test_file}"

@pytest.fixture
def create_test_html(tmp_path):
    def _create_file(html_content):
        test_file = tmp_path / "test.html"
        test_file.write_text(html_content)
        return f"file://{test_file}"
    return _create_file
    
class MockPlaywright:
    def __init__(self, html_content):
        self.html_content = html_content
        
    def chromium(self):
        return self
        
    def launch(self, headless=True):
        return self
        
    def new_page(self):
        return self
        
    def goto(self, url, timeout=0):
        pass  # Don't actually try to go to the URL
        
    def inner_html(self, selector):
        if selector == "#main_column":
            return self.html_content
        return ""

    def close(self):
        pass
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
@pytest.fixture
def listing_getter(sample_html):
    return ListingGetter(sample_html)

def test_reference_urls(listing_getter):
    refs = listing_getter.reference_urls
    assert len(refs) == 2
    assert refs[0] == "/wg-zimmer-in-Berlin-Mitte.123.html"
    assert refs[1] == "/wg-zimmer-in-Berlin-Wedding.456.html"

def test_user_names(listing_getter):
    users = listing_getter.user_names
    assert len(users) == 2
    assert users[0] == "John Doe"
    assert users[1] == "Jane Smith"

def test_rental_infos(listing_getter):
    addresses, wg_types = listing_getter.rental_infos
    assert len(addresses) == 2
    assert len(wg_types) == 2
    
    assert addresses[0] == "Mitte, Berlin"  # Fixed order
    assert wg_types[0] == "2er WG"
    
    assert addresses[1] == "Wedding, Berlin"
    assert wg_types[1] == "3er WG"

def test_rental_durations(listing_getter):
    rental_lengths = listing_getter.rental_durations
    assert len(rental_lengths) == 2
    assert rental_lengths[0] == 3  # May to August = 3 months
    assert rental_lengths[1] == -1  # Single date = unbefristet

def test_rental_start_dates(listing_getter):
    rental_starts = listing_getter.rental_start_dates
    assert len(rental_starts) == 2
    assert rental_starts[0] == datetime(2024, 5, 1)
    assert rental_starts[1] == datetime(2024, 6, 1)

def test_check_verified_business(listing_getter):
    results = listing_getter.check_verified_business()
    assert len(results) == 2
    assert results[0] == 0  # Not a verified company
    assert results[1] == 1  # Is a verified company

def test_all_infos(listing_getter):
    info_dict = listing_getter.all_infos
    assert len(info_dict) == 1  # Should only have one entry as second is verified company
    
    listing = info_dict[0]
    assert listing["ref"] == "/wg-zimmer-in-Berlin-Mitte.123.html"
    assert listing["user_name"] == "John Doe"
    assert listing["address"] == "Mitte, Berlin"  # Fixed order
    assert listing["wg_type"] == "2er WG"
    assert listing["rental_length_months"] == 3
    assert listing["rental_start"] == datetime(2024, 5, 1)

def test_compute_range_length():
    # Test the static helper method directly
    assert ListingGetter._compute_range_length("01.05.2024-01.08.2024") == 3
    assert ListingGetter._compute_range_length("01.12.2024-01.02.2025") == 2
    assert ListingGetter._compute_range_length("01.01.2024") == -1

def test_convert_to_datetime():
    result = ListingGetter._convert_to_datetime("01.05.2024")
    assert isinstance(result, datetime)
    assert result == datetime(2024, 5, 1)

def test_empty_and_single_listing(create_test_html):
    # Test empty HTML
    empty_url = create_test_html("<div id='main_column'></div>")
    empty_getter = ListingGetter(empty_url)
    assert len(empty_getter.listings) == 0

    # Test single listing HTML
    single_url = create_test_html("<div id='main_column'><div id='liste-details-ad-12345'></div></div>")
    single_getter = ListingGetter(single_url)
    assert len(single_getter.listings) == 1

def test_malformed_date_handling():
    # Should raise ValueError for malformed date
    with pytest.raises(ValueError):
        ListingGetter._convert_to_datetime("01-05-2024")  # Wrong format
        
    with pytest.raises(ValueError):
        ListingGetter._convert_to_datetime("2024.05.01")  # Wrong format
        
if __name__ == "__main__":
   # Set up the sample data
   temp_path = Path(os.getenv("WORKDIR", "."), "tests", "data", "sample.html")
   print("running")
   sample_html = f"file://{temp_path}"
   
   # Create listing_getter instance
   listing_getter = ListingGetter(sample_html)
   
   # Run all tests
   test_reference_urls(listing_getter)
   test_user_names(listing_getter)
   test_rental_infos(listing_getter)
   test_rental_durations(listing_getter)
   test_rental_start_dates(listing_getter)
   test_check_verified_business(listing_getter)
   test_all_infos(listing_getter)
   test_compute_range_length()
   test_convert_to_datetime()
   test_malformed_date_handling()
   print("All tests passed!")