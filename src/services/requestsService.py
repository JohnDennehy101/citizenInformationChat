

import requests

class RequestsService:
    def __init__(self, url):
        self.base_url = url
    
    def make_request(self, link):
        final_url = self.construct_url(link)
        print(f"Making request to url: {final_url}")
        r = requests.get(final_url)
        return r

    def construct_url(self, link):
        if link.startswith("https") or link.startswith("http"):
            return link
        else:
            return f"{self.base_url}{link}"

