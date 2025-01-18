"""Scrapes and processes WG-Gesucht.de listings to extract relevant rental information.

This module provides functionality to scrape WG-Gesucht.de listings and extract 
structured information about each rental listing, including references, usernames,
addresses, rental periods, and verification status.

Examples
--------
>>> url = "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html"
>>> listings_getter = ListingGetter(url)
>>> info_dict = listings_getter.get_all_infos()
>>> # Example output:
>>> {0: {
>>>     'ref': '/wg-zimmer-in-Berlin-Mitte.123.html',
>>>     'user_name': 'John Doe',
>>>     'address': 'Mitte, Berlin',
>>>     'wg_type': '2er WG',
>>>     'rental_length_months': 3,
>>>     'rental_start': datetime(2024, 5, 1)
>>> }}
"""
import pprint
import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class ListingGetter:
    """Handles the scraping and processing of WG-Gesucht.de listings.

    Uses Playwright to fetch dynamic content and BeautifulSoup to parse the HTML structure
    of WG-Gesucht.de listings, extracting relevant information about each rental offering.
    
    Parameters
    ----------
    url : str
        The complete WG-Gesucht.de search URL with all desired filters applied
    """
    def __init__(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=0)  # millisecond timeout
            html = page.inner_html("#main_column")

        soup = BeautifulSoup(html, "lxml")
        # get all listing elements by looking for 'liste-details-ad-#####'
        self.listings = soup.find_all("div", id=re.compile("^liste-details-ad-\d+"))

    @property
    def all_infos(self):
        """Extract all relevant information from the listings.

        Returns
        -------
        dict
            Dictionary where keys are listing indices and values are dictionaries
            containing listing details (ref, user_name, address, wg_type,
            rental_length_months, rental_start)

        Raises
        ------
        ValueError
            If the extracted listing information lists have inconsistent lengths
        """
        info_dict = {}
        refs = self.reference_urls
        user_names = self.user_names
        addresses, wg_types = self.rental_infos
        rental_lengths_months = self.rental_durations
        rental_starts = self.rental_start_dates
        is_verifiziertes_unternehmen = self.check_verified_business()

        # ensure all list are the same length
        lists = [
            refs,
            user_names,
            addresses,
            wg_types,
            rental_lengths_months,
            rental_starts,
        ]
        it = iter(lists)
        the_len = len(next(it))
        if not all(len(l) == the_len for l in it):
            raise ValueError("Not all lists have the same length!")

        # write dict for all listings
        for i, (
            ref,
            user_name,
            address,
            wg_type,
            rental_length_months,
            rental_start,
            verifiziertes_unternehmen,
        ) in enumerate(
            zip(
                refs,
                user_names,
                addresses,
                wg_types,
                rental_lengths_months,
                rental_starts,
                is_verifiziertes_unternehmen,
            )
        ):
            # skip promotes offers from letting agencies
            if "\n" in user_name:
                continue
            # skip sponsored offers
            if verifiziertes_unternehmen:
                continue

            listing_dict = {
                "ref": ref,
                "user_name": user_name,
                "address": address,
                "wg_type": wg_type,
                "rental_length_months": rental_length_months,
                "rental_start": rental_start,
            }

            info_dict[i] = listing_dict
        return info_dict

    @property
    def reference_urls(self):
        """Extract listing reference URLs.

        Returns
        -------
        List[str]
            List of strings containing the relative URLs for each listing
        """
        refs = list()
        for listing in self.listings:
            element = listing.find("a", href=True)
            refs.append(element["href"])
        return refs

    @property
    def user_names(self):
        """Extract usernames of listing creators.

        Returns
        -------
        List[str]
            List of strings containing the usernames for each listing
        """
        users = list()
        for listing in self.listings:
            element = listing.find("span", {"class": "ml5"})
            users.append(element.getText())
        return users

    @property
    def rental_infos(self):
        """Extract address and WG type information from listings.

        Returns
        -------
        tuple[List[str], List[str]]
            First list contains address strings (formatted as "district, city")
            Second list contains WG type strings (e.g., "2er WG")
        """
        address = list()
        wg_type = list()
        for listing in self.listings:
            element = listing.find("div", {"class": "col-xs-11"})
            text = element.find("span").getText()
            parts = [
                part.strip() for part in re.split("\||\n", text) if part.strip() != ""
            ]
            wg_type.append(parts[0])
            address.append(", ".join(parts[::-1][:-1]))
        return address, wg_type

    @property
    def rental_durations(self):
        """Calculate rental duration in months for each listing.

        Returns
        -------
        List[int]
            List of integers representing rental duration in months
            -1 indicates unlimited duration ("unbefristet")
        """
        rental_length_months = list()
        for listing in self.listings:
            element = listing.find("div", {"class": "col-xs-5 text-center"})
            text = element.getText()
            start_end = [
                part.strip() for part in re.split("-|\n", text) if part.strip() != ""
            ]
            rental_length_months.append(
                self._compute_range_length("-".join(start_end))
            )
        return rental_length_months

    @property
    def rental_start_dates(self):
        """Extract rental start dates from listings.

        Returns
        -------
        List[datetime]
            List of datetime objects representing the start date of each rental
        """
        rental_starts = list()
        for listing in self.listings:
            element = listing.find("div", {"class": "col-xs-5 text-center"})
            text = element.getText()
            start_end = [
                part.strip() for part in re.split("-|\n", text) if part.strip() != ""
            ]
            rental_starts.append(self._convert_to_datetime(start_end[0]))
        return rental_starts

    def check_verified_business(self) -> List[int]:
        """Check if listings are from verified businesses.

        Returns
        -------
        List[int]
            List of integers (0 or 1) indicating whether each listing is from 
            a verified business (1) or not (0)
        """
        is_verifiziertes_unternehmen = list()
        for listing in self.listings:
            status = 0
            element = listing.find("a", {"class": "campaign_click label_verified ml5"})
            if element:
                text = element.text.lower()
                if "unternehmen" in text:
                    status = 1
            is_verifiziertes_unternehmen.append(status)
        return is_verifiziertes_unternehmen

    @staticmethod
    def _convert_to_datetime(date: str) -> datetime:
        """Convert a date string to a datetime object.

        Parameters
        ----------
        date : str
            Date string in format "DD.MM.YYYY"

        Returns
        -------
        datetime
            Datetime object representing the rental start date
        """
        return datetime.strptime(date, "%d.%m.%Y")

    @staticmethod
    def _compute_range_length(date_range_str: str) -> int:
        """Calculate the rental duration in months from a date range string.

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
    url = "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html?csrf_token=c9280a89ddcd56ac55c721ab68f7c5fd64996ca7&offer_filter=1&city_id=8&sort_column=0&sort_order=0&noDeact=1&categories%5B%5D=0&rent_types%5B%5D=2&rent_types%5B%5D=1&rent_types%5B%5D=2%2C1&sMin=14&ot%5B%5D=126&ot%5B%5D=132&ot%5B%5D=85079&ot%5B%5D=151&ot%5B%5D=163&ot%5B%5D=85086&ot%5B%5D=165&wgSea=2&wgMnF=2&wgArt%5B%5D=6&wgArt%5B%5D=12&wgArt%5B%5D=11&wgArt%5B%5D=19&wgArt%5B%5D=22&wgSmo=2&exc=2&img_only=1"
    listings_getter = ListingGetter(url)
    info_dict = listings_getter.all_infos()
    pprint.pprint(info_dict)
