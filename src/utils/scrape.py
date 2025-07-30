import re
import os
import json

from constants import HTML_DIRECTORY_PATH, METADATA_DIRECTORY_PATH
from services.htmlParser import HTMLParser
from numpy import random
from time import sleep
from datetime import datetime

def scrape_files(scraped_files, file_service, requests_service, metadata_service, logger):
    for file_name in scraped_files:
        page_contents = file_service.read_from_file(HTML_DIRECTORY_PATH, file_name)

        page_html_parser = HTMLParser(page_contents)

        valid_links_for_scraping = page_html_parser.extract_valid_links()
        
        logger.info("*" * 5 + f" Valid urls found in {file_name}: {len(valid_links_for_scraping)} " + "*" * 5 )

        for i in range(0, len(valid_links_for_scraping)):
            request_sent = False
            link = valid_links_for_scraping[i]

            # This is required as there are relative path links in the documents e.g. ../en/social-welfare
            link = re.sub(r"\.\./(?:\.\./)*en", "/en", link)

            sanitised_file_name = file_service.sanitise_file_name(link)

            existing_files_metadata = file_service.read_from_file(METADATA_DIRECTORY_PATH, "file_metadata.json")

            existing_url_metadata_item = metadata_service.metadata_url_exists(existing_files_metadata, link)

            if not file_service.check_file_existence(HTML_DIRECTORY_PATH, sanitised_file_name):
                logger.info(f"{sanitised_file_name} does not exist, link: {link}")
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