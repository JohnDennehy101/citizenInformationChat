import os
from dotenv import load_dotenv
import logging
from services.fileService import FileService
from services.htmlParser import HTMLParser
from services.requestsService import RequestsService
from services.metadataService import MetadataService
from services.markdownService import MarkdownService
from services.dbService import DbService
from services.modelService import ModelService
from services.streamlitService import StreamlitService
from utils.config import read_command_arguments, initialiseDb
from utils.chunk import chunk_markdown_files
from utils.scrape import scrape_files
from utils.convertHtmlToMarkdown import convertHtmlToMarkdown
from constants import CHUNK_DIRECTORY_PATH, HTML_DIRECTORY_PATH, MARKDOWN_DIRECTORY_PATH, METADATA_DIRECTORY_PATH, SCRAPE_URL

logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logging.basicConfig(filename="webscrapercitizensinformation.log",  format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    flags = read_command_arguments()

    scrape_action, process_action, delete_markdown_files, delete_chunk_files, chunk_action, query_action = (flags["scrape_action"], flags["process_action"], flags["delete_markdown_files"], flags["delete_chunk_files"], flags["chunk_action"], flags["query_action"])

    file_service = FileService()
    markdown_service = MarkdownService()
    requests_service = RequestsService(SCRAPE_URL)
    metadata_service = MetadataService()
    dbService = DbService()
    model = ModelService(model_name)

    vectorDbConnection = initialiseDb(dbService)

    # Call this to make sure that directories are created where the data will be stored
    file_service.create_file_directory(HTML_DIRECTORY_PATH)
    file_service.create_file_directory(METADATA_DIRECTORY_PATH)
    file_service.create_file_directory(MARKDOWN_DIRECTORY_PATH)
    file_service.create_file_directory(CHUNK_DIRECTORY_PATH)

    scraped_files = [f for f in os.listdir(HTML_DIRECTORY_PATH) if os.path.isfile(os.path.join(HTML_DIRECTORY_PATH, f))]
    markdown_files = [f for f in os.listdir(MARKDOWN_DIRECTORY_PATH) if os.path.isfile(os.path.join(MARKDOWN_DIRECTORY_PATH, f))]
    chunked_markdown_files = [f for f in os.listdir(CHUNK_DIRECTORY_PATH) if os.path.isfile(os.path.join(CHUNK_DIRECTORY_PATH, f))]

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
        scrape_files(scraped_files, file_service, requests_service, metadata_service, logger)
    
    if process_action:
        logging.info("*" * 5 + f"Beginning processing process" + "*" * 5 )
        convertHtmlToMarkdown(scraped_files, file_service, markdown_service, logger)
    
    if chunk_action:
        logging.info("*" * 5 + f"Beginning chunking process" + "*" * 5 )
        chunk_markdown_files(markdown_files, file_service, markdown_service, logger)
    
    if query_action:
        logging.info("*" * 5 + f"Beginning query process" + "*" * 5 )

        streamlit = StreamlitService(vectorDbConnection, model)

        streamlit.render_user_interface()

        try:
            for file_name in markdown_files:
                chunk_file_names = file_service.read_directory_contents(f'{CHUNK_DIRECTORY_PATH}/{file_name}')

                for individual_chunk_file_name in chunk_file_names:
                    markdown_content = file_service.read_from_file(f'{CHUNK_DIRECTORY_PATH}/{file_name}', individual_chunk_file_name)
                    markdown_chunks = model.chunk_text(markdown_content, 8192)

                    for chunk in markdown_chunks:
                        markdown_chunk_embedding = model.get_embedding(chunk)
                        dbService.store_embedding(vectorDbConnection, chunk, markdown_chunk_embedding)
        except Exception as e:
            logging.info(e)
        
        
        
if __name__ == "__main__":
    main()
