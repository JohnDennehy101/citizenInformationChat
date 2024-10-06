import re
from bs4 import BeautifulSoup
import logging
logger = logging.getLogger(__name__)

class HTMLParser:
    def __init__(self, html_content):
        self.soup_instance = BeautifulSoup(html_content, "html.parser")

    def extract_valid_links(self):
        a_tags = self.soup_instance.find_all("a", href=True)
        valid_links = [tag["href"] for tag in a_tags if self.valid_link(tag["href"])]
        return valid_links
    
    def valid_link(self, link):
        if (not link or 
            link.startswith("#") or 
            link.startswith("county") or 
            link.startswith("centre") or 
            link.startswith("javascript:") or 
            link.startswith("whatsapp") or 
            link.startswith("tel:") or 
            "facebook" in link or
            "twitter" in link or
            (re.match(r"https?:\/\/", link) and not "citizensinformation.ie" in link)):
            return False
        return True
    
    def sanitise_html_content(self):
        try:
            cookie_banner_element = self.soup_instance.find("div", id="cookies-banner")

            if cookie_banner_element:
                cookie_banner_element.extract()
            
            cookie_modal_element = self.soup_instance.find("div", id="modal_cookies")

            if cookie_modal_element:
                cookie_modal_element.extract()

            cookie_footer_wrapper_element = self.soup_instance.find("div", class_="cookiejs-footer-wrapper")

            if cookie_footer_wrapper_element:
                cookie_footer_wrapper_element.extract()
            
            nav_item_elements = self.soup_instance.find_all("nav")

            for nav_item in nav_item_elements:
                nav_item.extract()

            footer_element = self.soup_instance.find("footer")

            if footer_element:
                footer_element.extract()
            
            invisible_links = self.soup_instance.find_all("a", class_="invisible")

            for link in invisible_links:
                link.extract()
            
            image_elements = self.soup_instance.find_all("img")

            logo_link_element = self.soup_instance.find("span", class_="logo_link")

            if logo_link_element:
                logo_link_element.extract()

            for image_element in image_elements:
                image_element.extract()

            return self.soup_instance.prettify()

        except Exception as e:
            logger.info(f"Error sanitising html: {e}")
            return None