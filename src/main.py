import requests
import urllib.parse
import re
import os
from bs4 import BeautifulSoup
from numpy import random
from time import sleep
from services.fileService import FileService
from services.htmlParser import HTMLParser
from services.requestsService import RequestsService

def main():
    file_service = FileService("src/pages")
    requests_service = RequestsService("https://www.citizensinformation.ie")
    
    home_page_contents = file_service.read_from_file("home_page.html")

    home_page_html_parser = HTMLParser(home_page_contents)

    valid_links_for_scraping = home_page_html_parser.extract_valid_links()

    print(f"Valid urls found in home_page.html: {len(valid_links_for_scraping)}")

    for i in range(0, 50):
        request_sent = False
        link = valid_links_for_scraping[i]

        sanitised_file_name = file_service.sanitise_file_name(link)

        file_service.check_file_existence("home_page.html")

        if not file_service.check_file_existence(sanitised_file_name):
            request_sent = True
            # Make Request
            response = requests_service.make_request(link)

            # Write to file
            write_file_contents_successful = file_service.write_to_file(sanitised_file_name, response.text)

            if write_file_contents_successful:
                print(f"Writing {sanitised_file_name} successful")
            else:
                print(f"Writing {sanitised_file_name} was not successful")

        else:
            print(f"{sanitised_file_name} already exists, skipping...")

        if request_sent:
            sleep_time = random.uniform(2, 4)
            print(f"Breaking between requests for {sleep_time} seconds")
            sleep(sleep_time)







if __name__ == "__main__":
    main()
