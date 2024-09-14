from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class MetadataService:
    def generate_metadata(self, url, file_name, file_path, link_found_in_page):
        return {"url": url, "fileName": file_name, "path": file_path, "created": datetime.now().isoformat(), "linkPageSource": link_found_in_page}