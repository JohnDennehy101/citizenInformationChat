from datetime import datetime
import logging
import json
from constants import SCRAPE_URL
logger = logging.getLogger(__name__)

class MetadataService:
    def generate_metadata_url(self, url):
        if url.startswith("/"):
            return f"{SCRAPE_URL}{url}"
        return url

    def generate_new_metadata_item(self, url, file_name, file_path, link_found_in_page):
        return {"url": self.generate_metadata_url(url), "fileName": file_name, "path": file_path, "created": datetime.now().isoformat(), "lastUpdated": datetime.now().isoformat(), "linkPageSources": [link_found_in_page]}
    
    def metadata_url_exists(self, existing_files_metadata, url):
        if not existing_files_metadata:
            return False
        
        for item in existing_files_metadata:

            if isinstance(item, dict) and item.get("url") == self.generate_metadata_url(url):
                return item

        return False
    
    def update_metadata_contents(self, url, existing_files_metadata, updated_item):
        updated = False
        if existing_files_metadata:
            for item in existing_files_metadata:
                if item.get("url") == self.generate_metadata_url(url):
                    item.update(updated_item)
                    updated = True
                    break

        if not updated:
            existing_files_metadata.append(updated_item)

        return existing_files_metadata
        