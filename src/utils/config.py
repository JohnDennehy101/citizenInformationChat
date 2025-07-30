import argparse
import os


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

    flags = {
        "scrape_action": args.scrape,
        "process_action": args.process,
        "delete_markdown_files": args.delete_markdown_files,
        "chunk_action": args.chunk,
        "delete_chunk_files": args.delete_chunk_files,
    }
    return flags

