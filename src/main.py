import requests
import urllib.parse
import re
import os
import json
import logging
import argparse
from bs4 import BeautifulSoup
from numpy import random
from time import sleep
from services.fileService import FileService
from services.htmlParser import HTMLParser
from services.requestsService import RequestsService
from services.metadataService import MetadataService
from services.markdownService import MarkdownService
from utils.config import read_command_arguments
from datetime import datetime
from constants import CHUNK_DIRECTORY_PATH, HTML_DIRECTORY_PATH, MARKDOWN_DIRECTORY_PATH, METADATA_DIRECTORY_PATH, SCRAPE_URL

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename="webscrapercitizensinformation.log",  format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    flags = read_command_arguments()

    scrape_action, process_action, delete_markdown_files, delete_chunk_files, chunk_action = (flags["scrape_action"], flags["process_action"], flags["delete_markdown_files"], flags["delete_chunk_files"], flags["chunk_action"])

    file_service = FileService()
    markdown_service = MarkdownService()

    # Call this to make sure that directories are created where the data will be stored
    file_service.create_file_directory(HTML_DIRECTORY_PATH)
    file_service.create_file_directory(METADATA_DIRECTORY_PATH)
    file_service.create_file_directory(MARKDOWN_DIRECTORY_PATH)
    file_service.create_file_directory(CHUNK_DIRECTORY_PATH)

    scraped_files = [f for f in os.listdir(HTML_DIRECTORY_PATH) if os.path.isfile(os.path.join(HTML_DIRECTORY_PATH, f))]
    markdown_files = [f for f in os.listdir(MARKDOWN_DIRECTORY_PATH) if os.path.isfile(os.path.join(MARKDOWN_DIRECTORY_PATH, f))]

    # Call this to create file metadata file if it does not exist
    if not file_service.check_file_existence(METADATA_DIRECTORY_PATH, "file_metadata.json"):
        file_service.write_to_file(METADATA_DIRECTORY_PATH, "file_metadata.json", [])

    
    if delete_markdown_files:
        logging.info("*" * 5 + f"Clearing markdown files directory" + "*" * 5 )
        file_service.clear_file_directory(MARKDOWN_DIRECTORY_PATH)
        logging.info("*" * 5 + f"Successfully cleared markdown files directory" + "*" * 5 )
    
    if delete_chunk_files:
        logging.info("*" * 5 + f"Clearing chunk files directory" + "*" * 5 )
        file_service.clear_file_directory(CHUNK_DIRECTORY_PATH)
        logging.info("*" * 5 + f"Successfully cleared chunk files directory" + "*" * 5 )

    if scrape_action:
        logging.info("*" * 5 + f"Beginning scraping process" + "*" * 5 )

        requests_service = RequestsService(SCRAPE_URL)

        metadata_service = MetadataService()

        for file_name in scraped_files:
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
    
    if process_action:
        logging.info("*" * 5 + f"Beginning processing process" + "*" * 5 )

        for file_name in scraped_files:
            markdown_file_name = file_name.replace(".html", ".md")

            if not file_service.check_file_existence(MARKDOWN_DIRECTORY_PATH, markdown_file_name):
                logging.info(f"Markdown file does not exist for {file_name}")

                page_contents = file_service.read_from_file(HTML_DIRECTORY_PATH, file_name)

                page_html_parser = HTMLParser(page_contents)

                sanitised_html_content = page_html_parser.sanitise_html_content()

                # Initialise to None
                markdown_response = None

                if sanitised_html_content:
                    markdown_response = markdown_service.convert_html_to_markdown(sanitised_html_content)
                else:
                    logger.info(f"Error when sanitising html for file {file_name}")

                if markdown_response:
                    # Write to markdown file
                    write_file_contents_successful = file_service.write_to_file(MARKDOWN_DIRECTORY_PATH, markdown_file_name, markdown_response)

                    if write_file_contents_successful:
                        logger.info(f"Writing {markdown_file_name} markdown successful")
                    else:
                        logger.info(f"Writing {markdown_file_name} markdown was not successful")
    
    if chunk_action:
        logging.info("*" * 5 + f"Beginning chunking process" + "*" * 5 )

        for file_name in markdown_files:

            if not file_service.check_file_existence(CHUNK_DIRECTORY_PATH, file_name):
                logging.info(f"Chunk file does not exist for {file_name}")

                markdown_content = file_service.read_from_file(MARKDOWN_DIRECTORY_PATH, file_name)

                if markdown_content:
                    chunked_markdown_content = markdown_service.chunk_markdown(markdown_content)

                    file_service.create_file_directory(f'{CHUNK_DIRECTORY_PATH}/{file_name}')

                    for i, chunk in enumerate(chunked_markdown_content, start=1):
                        write_file_contents_successful = file_service.write_to_file(f'{CHUNK_DIRECTORY_PATH}/{file_name}', f'chunk_{i}.md', chunk)

                        if write_file_contents_successful:
                            logger.info(f"Writing {f'chunk{i}'} chunk for {file_name} successful")
                        else:
                            logger.info(f"Writing {f'chunk_{i}'} chunk for {file_name} was not successful")



if __name__ == "__main__":
    main()
