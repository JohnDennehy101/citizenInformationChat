from bs4 import BeautifulSoup

class HTMLParser:
    def __init__(self, html_content):
        self.soup_instance = BeautifulSoup(html_content, "html.parser")

    def extract_valid_links(self):
        a_tags = self.soup_instance.find_all("a", href=True)
        valid_links = [tag["href"] for tag in a_tags if self.valid_link(tag["href"])]
        return valid_links
    
    def valid_link(self, link):
        if not link or link.startswith("#") or link.startswith("javascript:") or link.startswith("tel:"):
            return False
        return True