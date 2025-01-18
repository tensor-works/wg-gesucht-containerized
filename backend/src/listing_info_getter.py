# in src folder
"""Retrieves and processes detailed information from individual WG-Gesucht.de listings.

This module handles the extraction of specific information from individual WG-Gesucht.de 
listing pages, including listing descriptions and rental duration details.

Examples
--------
>>> getter = ListingInfoGetter("/wg-zimmer-in-Berlin-Mitte.123.html")
>>> text = getter.listing_text
>>> # Example output:
>>> "Bright room in the heart of Berlin...\n\nClose to public transport...\n\n"
>>> 
>>> duration = getter.rental_duration_months
>>> print(duration)
3
"""
import json
import os
import re

import requests
from bs4 import BeautifulSoup


class ListingInfoGetter:
    """Handles retrieval and processing of individual WG-Gesucht.de listings.

    Fetches and parses individual listing pages to extract detailed information
    about each rental offering.

    Parameters
    ----------
    ref : str
        The listing reference URL (relative path from wg-gesucht.de)
    """

    def __init__(self, ref: str):
        url_base = "https://www.wg-gesucht.de"
        url = url_base + ref
        self.r = requests.get(url).text

    @property
    def listing_text(self) -> str:
        """Extract and format the listing description text.

        Returns
        -------
        str
            The formatted listing description text with headers and paragraphs
            separated by double newlines
        """
        soup = BeautifulSoup(self.r, "lxml")
        ad_description = soup.find("div", {"id": "ad_description_text"}).find_all(
            ["p", "h3"]
        )
        text = []
        for chunk in ad_description:
            text.extend([chunk.getText().strip(), "\n\n"])
        text = "".join(text)
        return text

    @staticmethod
    def save_listing_text(file_name: str, text: str) -> None:
        """Save listing text to a JSON file.

        Parameters
        ----------
        file_name : str
            Path to the JSON file where texts should be saved
        text : str
            The listing text to be saved

        Notes
        -----
        If the file doesn't exist, it will be created with an initial text.
        If it exists, the new text will be appended to the existing texts.
        """
        if not os.path.exists(file_name):
            data = {"texts": [text]}
            with open(file_name, "w") as f:
                json.dump(data, f)

        with open(file_name, "r+") as f:
            data = json.load(f)
            data["texts"].append(text)
            f.seek(0)
            json.dump(data, f)

    @property
    def rental_duration_months(self) -> int:
        """Calculate the rental duration in months.

        Returns
        -------
        int
            Number of months between start and end date, or -1 for unlimited duration

        Raises
        ------
        ValueError
            If rental dates cannot be found in the listing
        """
        soup = BeautifulSoup(self.r, "lxml")
        ps = soup.find_all("p", {"style": "line-height: 2em;"})
        dates = []
        for i, p in enumerate(ps):
            text = p.getText().strip()
            if "frei ab:" in text:
                text = text.replace("  ", "")
                dates = [elem for elem in re.split(" |\n", text) if "." in elem]
        if dates:
            return self._compute_rental_duration("-".join(dates))
        else:
            raise ValueError("Could not get rental dates!")

    @staticmethod
    def _compute_rental_duration(date_range_str: str) -> int:
        """Calculate the duration in months between two dates.

        Parameters
        ----------
        date_range_str : str
            String containing start and end dates ("DD.MM.YYYY-DD.MM.YYYY")
            or single date for unlimited duration

        Returns
        -------
        int
            Number of months between start and end date, or -1 for unlimited duration
        """
        dates = date_range_str.split("-")
        if len(dates) != 2:
            # means listing is 'unbefristet'
            return -1
        start, end = date_range_str.split("-")
        start, end = start.strip(), end.strip()

        # year, month, day
        start_day, start_month, start_year = start.split(".")
        end_day, end_month, end_year = end.split(".")

        # get time difference in months
        date_diff = (int(end_year) - int(start_year)) * 12 + (
            int(end_month) - int(start_month)
        )
        return date_diff


if __name__ == "__main__":
    getter = ListingInfoGetter("/wg-zimmer-in-Berlin-Charlottenburg.9848754.html")
    # print(getter.listing_text)
    print(getter.rental_duration_months)