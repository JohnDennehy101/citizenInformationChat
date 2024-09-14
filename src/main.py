import requests
import urllib.parse
import re
import os
import json
import logging
from bs4 import BeautifulSoup
from numpy import random
from time import sleep
from services.fileService import FileService
from services.htmlParser import HTMLParser
from services.requestsService import RequestsService
from services.metadataService import MetadataService

HTML_DIRECTORY_PATH = "data/html"
METADATA_DIRECTORY_PATH = "data/metadata"
SCRAPE_URL = "https://www.citizensinformation.ie"

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename="webscrapercitizensinformation.log",  format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    scraped_files = [f for f in os.listdir(HTML_DIRECTORY_PATH) if os.path.isfile(os.path.join(HTML_DIRECTORY_PATH, f))]

    file_service = FileService()

    # Call this to make sure that directories are created where the data will be stored
    file_service.create_file_directory(HTML_DIRECTORY_PATH)
    file_service.create_file_directory(METADATA_DIRECTORY_PATH)

    requests_service = RequestsService(SCRAPE_URL)

    metadata_service = MetadataService()

    # This commented out line used to run all
    # for file_name in scraped_file:
    for file_name in scraped_files[:2]:
        page_contents = file_service.read_from_file(HTML_DIRECTORY_PATH, file_name)

        page_html_parser = HTMLParser(page_contents)

        valid_links_for_scraping = page_html_parser.extract_valid_links()
        
        logging.info(f"Valid urls found in {file_name}: {len(valid_links_for_scraping)}")

        for i in range(0, 2):
            request_sent = False
            link = valid_links_for_scraping[i]

            sanitised_file_name = file_service.sanitise_file_name(link)

            if not file_service.check_file_existence(HTML_DIRECTORY_PATH, sanitised_file_name):
                logging.info(f"{sanitised_file_name} does not exist, link: {link}")
                request_sent = True

                # Make Request
                response = requests_service.make_request(link)

                if response:
                    # Write to file
                    write_file_contents_successful = file_service.write_to_file(HTML_DIRECTORY_PATH, sanitised_file_name, response.text)

                    if write_file_contents_successful:
                        logger.info(f"Writing {sanitised_file_name} successful")

                        new_file_metadata = metadata_service.generate_metadata(link, sanitised_file_name, os.path.join(HTML_DIRECTORY_PATH, sanitised_file_name), file_name)

                        new_file_metadata_json = json.dumps(new_file_metadata)

                        if not file_service.check_file_existence(METADATA_DIRECTORY_PATH, "file_metadata.json"):
                             file_service.write_to_file(METADATA_DIRECTORY_PATH, "file_metadata.json", json.dumps([]))

                        #existing_metadata_json = file_service.read_from_file(METADATA_DIRECTORY_PATH, "file_metadata.json")


                        #new_metadata_json = existing_metadata_json.append(new_file_metadata_json)

                        file_service.append_to_file(METADATA_DIRECTORY_PATH, "file_metadata.json", new_file_metadata)

                        logger.info(f"Writing {sanitised_file_name} metadata successful")
                    else:
                        logger.info(f"Writing {sanitised_file_name} was not successful")

            else:
                logger.info(f"{sanitised_file_name} already exists, skipping...")

            if request_sent:
                sleep_time = random.uniform(2, 5)
                logger.info(f"Breaking between requests for {sleep_time} seconds")
                sleep(sleep_time)



if __name__ == "__main__":
    main()
