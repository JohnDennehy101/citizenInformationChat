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

    def chunk_markdown(self, markdown_content):
        chunks = []
        current_chunk = []

        for line in markdown_content.splitlines():
            if line.startswith("##"):
                chunks.append("\n".join(current_chunk))
                current_chunk = []

            current_chunk.append(line)
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
            

