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
from datetime import datetime
from constants import HTML_DIRECTORY_PATH, METADATA_DIRECTORY_PATH, SCRAPE_URL

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

    # Call this to create file metadata file if it does not exist
    if not file_service.check_file_existence(METADATA_DIRECTORY_PATH, "file_metadata.json"):
        file_service.write_to_file(METADATA_DIRECTORY_PATH, "file_metadata.json", [])

    requests_service = RequestsService(SCRAPE_URL)

    metadata_service = MetadataService()

    # This commented out line used to run all
    # for file_name in scraped_file:
    for file_name in scraped_files[:5]:
        page_contents = file_service.read_from_file(HTML_DIRECTORY_PATH, file_name)

        page_html_parser = HTMLParser(page_contents)

        valid_links_for_scraping = page_html_parser.extract_valid_links()
        
        logging.info("*" * 5 + f" Valid urls found in {file_name}: {len(valid_links_for_scraping)} " + "*" * 5 )

        for i in range(0, len(valid_links_for_scraping)):
            request_sent = False
            link = valid_links_for_scraping[i]

            # This is required as there are relative path links in the documents e.g. ../en/social-welfare
            link = re.sub(r"\.\./(?:\.\./)*en", "/en", link)

            sanitised_file_name = file_service.sanitise_file_name(link)

            existing_files_metadata = file_service.read_from_file(METADATA_DIRECTORY_PATH, "file_metadata.json")

            existing_url_metadata_item = metadata_service.metadata_url_exists(existing_files_metadata, link)

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
                    else:
                        logger.info(f"Writing {sanitised_file_name} was not successful")

            else:
                logger.info(f"{sanitised_file_name} already exists, skipping...")

            if request_sent:
                sleep_time = random.uniform(2, 5)
                logger.info(f"Breaking between requests for {sleep_time} seconds")
                sleep(sleep_time)
            
            # Always run this to updated files metadata - only if file exists - has been created or updated
            if file_service.check_file_existence(HTML_DIRECTORY_PATH, sanitised_file_name):
                if not existing_url_metadata_item:
                    url_metadata = metadata_service.generate_new_metadata_item(link, sanitised_file_name, os.path.join(HTML_DIRECTORY_PATH, sanitised_file_name), file_name)
                    url_metadata_json = json.dumps(url_metadata)
                    new_files_metadata = metadata_service.update_metadata_contents(link, existing_files_metadata, url_metadata)
                else:
                    if sanitised_file_name not in existing_url_metadata_item["linkPageSources"]:
                        existing_url_metadata_item["linkPageSources"].append(sanitised_file_name)
                        existing_url_metadata_item["lastUpdated"] = datetime.now().isoformat()
                    new_files_metadata = metadata_service.update_metadata_contents(link, existing_files_metadata, existing_url_metadata_item)
                    
                file_service.write_to_file(METADATA_DIRECTORY_PATH, "file_metadata.json", new_files_metadata)
                logger.info(f"Writing {sanitised_file_name} metadata successful")



if __name__ == "__main__":
    main()
