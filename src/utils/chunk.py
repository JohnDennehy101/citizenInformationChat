from constants import CHUNK_DIRECTORY_PATH, MARKDOWN_DIRECTORY_PATH

def chunk_markdown_files(markdown_files, file_service, markdown_service, logger):
    for file_name in markdown_files:
        if not file_service.check_file_existence(CHUNK_DIRECTORY_PATH, file_name):
            logger.info(f"Chunk file does not exist for {file_name}")

            markdown_content = file_service.read_from_file(MARKDOWN_DIRECTORY_PATH, file_name)

            if markdown_content:
                chunked_markdown_content = markdown_service.chunk_markdown(markdown_content)

                file_service.create_file_directory(f'{CHUNK_DIRECTORY_PATH}/{file_name}')

                for i, chunk in enumerate(chunked_markdown_content, start=1):
                    write_file_contents_successful = file_service.write_to_file(f'{CHUNK_DIRECTORY_PATH}/{file_name}', f'chunk_{i}.md', chunk)

                    if write_file_contents_successful:
                        logger.info(f"Writing {f'chunk{i}'} chunk for {file_name} successful")
                    else:
                        logger.info(f"Writing {f'chunk_{i}'} chunk for {file_name} was not successful")