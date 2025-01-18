import pytest
import json
import os
from unittest.mock import patch
from pathlib import Path
from src.listing_info_getter import ListingInfoGetter

@pytest.fixture
def listing_html():
    return """<!DOCTYPE html>
<html>
<body>
    <div id="ad_description_text">
        <h3>About the apartment</h3>
        <p>This is a great apartment in the heart of Berlin.</p>
        <h3>About the area</h3>
        <p>Close to public transport and shops.</p>
    </div>
    <p style="line-height: 2em;">
        frei ab: 01.05.2024 - 01.08.2024
    </p>
</body>
</html>
"""

@pytest.fixture
def mock_response(listing_html):
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = listing_html
        yield mock_get

@pytest.fixture
def info_getter(mock_response):
    return ListingInfoGetter("/wg-zimmer-test.html")

def test_listing_text(info_getter):
    text = info_getter.listing_text
    expected = "About the apartment\n\nThis is a great apartment in the heart of Berlin.\n\nAbout the area\n\nClose to public transport and shops.\n\n"
    assert text == expected

def test_rental_duration_months(info_getter):
    months = info_getter.rental_duration_months
    assert months == 3  # May to August is 3 months

def test_compute_rental_duration():
    # Test regular date range
    assert ListingInfoGetter._compute_rental_duration("01.05.2024-01.08.2024") == 3
    
    # Test year boundary
    assert ListingInfoGetter._compute_rental_duration("01.12.2024-01.02.2025") == 2
    
    # Test unbefristet
    assert ListingInfoGetter._compute_rental_duration("01.05.2024") == -1

def test_save_listing_text(tmp_path):
    file_path = tmp_path / "test_listings.json"
    test_text = "Sample listing text"
    
    # Test creating new file
    ListingInfoGetter.save_listing_text(str(file_path), test_text)
    
    with open(file_path) as f:
        data = json.load(f)
        assert "texts" in data
        assert test_text in data["texts"]
    
    # Test appending to existing file
    new_text = "Another listing text"
    ListingInfoGetter.save_listing_text(str(file_path), new_text)
    
    with open(file_path) as f:
        data = json.load(f)
        assert len(data["texts"]) > 1
        assert test_text in data["texts"]
        assert new_text in data["texts"]

def test_rental_duration_no_dates():
    html_without_dates = """
    <html><body>
        <p style="line-height: 2em;">Some text without dates</p>
    </body></html>
    """
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = html_without_dates
        getter = ListingInfoGetter("/test.html")
        
        with pytest.raises(ValueError, match="Could not get rental dates!"):
            _ = getter.rental_duration_months

def test_malformed_date_format():
    # Test with missing end date (unbefristet)
    assert ListingInfoGetter._compute_rental_duration("01.05.2024") == -1
    
    # Test with invalid date format that should still parse
    result = ListingInfoGetter._compute_rental_duration("01.12.2024 - 01.02.2025")
    assert result == 2

@pytest.mark.parametrize("html,expected_text", [
    ("""
    <div id="ad_description_text">
        <p>Single paragraph</p>
    </div>
    """, "Single paragraph\n\n"),
    ("""
    <div id="ad_description_text">
        <h3>Title</h3>
        <p>Content</p>
    </div>
    """, "Title\n\nContent\n\n"),
])
def test_different_text_formats(html, expected_text):
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = html
        getter = ListingInfoGetter("/test.html")
        assert getter.listing_text == expected_text