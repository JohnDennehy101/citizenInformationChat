

import requests
import logging
logger = logging.getLogger(__name__)

class RequestsService:
    def __init__(self, url):
        self.base_url = url
    
    def make_request(self, link):
        try:
            final_url = self.construct_url(link)
            logger.info(f"Making request to url: {final_url}")
            r = requests.get(final_url, timeout=3)
            return r
        except:
            return None
            logger.info(f"URL did not result in correct response: {final_url}")

    def construct_url(self, link):
        if link.startswith("https") or link.startswith("http") or link.startswith("centres"):
            return link
        else:
            return f"{self.base_url}{link}"

