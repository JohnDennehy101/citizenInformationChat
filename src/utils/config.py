import argparse
import os
from pgvector.psycopg2 import register_vector
from streamlit.runtime.scriptrunner import get_script_run_ctx


def add_command_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-s",
            "--scrape",
            action="store_true")
    parser.add_argument(
            "-p",
            "--process",
            action="store_true")
    parser.add_argument(
            "-c",
            "--chunk",
            action="store_true")
    parser.add_argument(
            "-dmf",
            "--delete-markdown-files",
            action="store_true")
    parser.add_argument(
            "-dcf",
            "--delete-chunk-files",
            action="store_true")
    
    return parser.parse_args()

def read_command_arguments():
    args = add_command_arguments()
    query_action = False

    if get_script_run_ctx():
        query_action = True

    flags = {
        "scrape_action": args.scrape,
        "process_action": args.process,
        "delete_markdown_files": args.delete_markdown_files,
        "chunk_action": args.chunk,
        "delete_chunk_files": args.delete_chunk_files,
        "query_action": query_action
    }
    return flags

def initialiseDb(dbService):
    # TODO: Add error handling for this
    dbHost = os.getenv("DB_HOST")
    coreDbName = os.getenv("CORE_DB_NAME")
    vectorDbName = os.getenv("VECTOR_DB_NAME")
    userName = os.getenv("DB_USERNAME")

    coreDbConnection = dbService.connect(dbHost, coreDbName, userName)

    vectorDbExists = dbService.check_db_existence(coreDbConnection, vectorDbName)

    if not vectorDbExists:
        dbService.create_database(coreDbConnection, vectorDbName)
    
    dbService.close_connection(coreDbConnection)

    vectorDbConnection = dbService.connect(dbHost, vectorDbName, userName)
    
    dbService.enable_vector_extension(vectorDbConnection)

    #register the vector type with psycopg2
    register_vector(vectorDbConnection)

    dbService.create_embeddings_table(vectorDbConnection)

    dbService.clean_embeddings_table(vectorDbConnection)

    return vectorDbConnection

