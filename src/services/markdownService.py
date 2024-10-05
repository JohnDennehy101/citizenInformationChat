import html2text
import logging
logger = logging.getLogger(__name__)

class MarkdownService:
    def __init__(self):
        self.markdown_instance = html2text.HTML2Text()

    def convert_html_to_markdown(self, html_content):
        try:
            markdown = self.markdown_instance.handle(html_content)
            return markdown
        except Exception as e:
            logger.info(f"An error occurred when converting html to markdown: {e}")
            return None
