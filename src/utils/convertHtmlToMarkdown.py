from constants import HTML_DIRECTORY_PATH, MARKDOWN_DIRECTORY_PATH

def convertHtmlToMarkdown(scraped_files, file_service, markdown_service, logger):
    for file_name in scraped_files:
        markdown_file_name = file_name.replace(".html", ".md")

        if not file_service.check_file_existence(MARKDOWN_DIRECTORY_PATH, markdown_file_name):
            logger.info(f"Markdown file does not exist for {file_name}")

            page_contents = file_service.read_from_file(HTML_DIRECTORY_PATH, file_name)

            page_html_parser = HTMLParser(page_contents)

            sanitised_html_content = page_html_parser.sanitise_html_content()

            # Initialise to None
            markdown_response = None

            if sanitised_html_content:
                markdown_response = markdown_service.convert_html_to_markdown(sanitised_html_content)
            else:
                logger.info(f"Error when sanitising html for file {file_name}")

            if markdown_response:
                # Write to markdown file
                write_file_contents_successful = file_service.write_to_file(MARKDOWN_DIRECTORY_PATH, markdown_file_name, markdown_response)

                if write_file_contents_successful:
                    logger.info(f"Writing {markdown_file_name} markdown successful")
                else:
                    logger.info(f"Writing {markdown_file_name} markdown was not successful")
        else:
            logger.info(f"Markdown file already exists for {file_name}")
