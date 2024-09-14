import requests
import urllib.parse
import re
import os
import logging
from bs4 import BeautifulSoup
from numpy import random
from time import sleep
from services.fileService import FileService
from services.htmlParser import HTMLParser
from services.requestsService import RequestsService

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename="webscrapercitizensinformation.log",  format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    file_name_to_parse = "home_page.html"

    file_service = FileService("src/pages")
    requests_service = RequestsService("https://www.citizensinformation.ie")

    page_contents = file_service.read_from_file(file_name_to_parse)

    page_html_parser = HTMLParser(page_contents)

    valid_links_for_scraping = page_html_parser.extract_valid_links()
    

    logging.info(f"Valid urls found in ${file_name_to_parse}: {len(valid_links_for_scraping)}")

    for i in range(0, len(valid_links_for_scraping)):
        request_sent = False
        link = valid_links_for_scraping[i]

        sanitised_file_name = file_service.sanitise_file_name(link)

        if not file_service.check_file_existence(sanitised_file_name):
            logging.info(f"{sanitised_file_name} does not exist, link: {link}")
            request_sent = True
            # Make Request
            response = requests_service.make_request(link)

            # Write to file
            write_file_contents_successful = file_service.write_to_file(sanitised_file_name, response.text)

            if write_file_contents_successful:
                logger.info(f"Writing {sanitised_file_name} successful")
            else:
                logger.info(f"Writing {sanitised_file_name} was not successful")

        else:
            logger.info(f"{sanitised_file_name} already exists, skipping...")

        if request_sent:
            sleep_time = random.uniform(2, 8)
            logger.info(f"Breaking between requests for {sleep_time} seconds")
            sleep(sleep_time)



if __name__ == "__main__":
    main()
