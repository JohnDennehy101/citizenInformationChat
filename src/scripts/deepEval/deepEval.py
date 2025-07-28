import json
import os
import re
import concurrent.futures
import time
import asyncio

from datetime import datetime
from deepeval.metrics import (
  ContextualRelevancyMetric,
  ContextualRecallMetric,
  ContextualPrecisionMetric,
  AnswerRelevancyMetric,
  FaithfulnessMetric
)
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from more_itertools import chunked
from typing import Optional, List, Tuple, Any, Union, Pattern, Dict, Callable

def check_file_exists(file_path: str) -> bool:
  """
  This function checks if provided file path exists

  Args:
    file_path (str): file path which should be checked for file existence
  
  Returns:
    bool: whether the file exists or not
  """

  # Uses os package isfile method to determine if a file exists at the provided file path
  # If so, return True, else return False
  if os.path.isfile(file_path):
    return True

  return False


def read_json_file(input_file_path: str, default: Any = []) -> Any:
  """
  Reads content from json file at provided input file path

  Args:
    input_file_path (str): the file path where the target file resides
    default (Any): the default structure of the expected file (to be returned in case of error to avoid consuming errors)
  
  Returns:
    Any: the content read from the file
  """

  # Call utility function to check if a file actually exists at the provided file path parameter
  # If it does not exist, return the default data structure
  if not check_file_exists(input_file_path):
    return default

  # Try open the file and read the contents
  # If successful, return the contents. If not successful, return the default data structure
  try:
    with open(input_file_path, "r", encoding="utf-8") as input_file:
      content = json.load(input_file)

    print("Successfully loaded content from {} file".format(input_file_path))
    return content

  except (OSError, IOError, json.JSONDecodeError) as e:
    print("Error reading from file path: {}".format(input_file_path))
    return default


def write_json_file(output_file_path: str, content: Any) -> bool:
  """
  Writes content to json file at provided output path

  Args:
    output_file_path (str): File path at which file should be generated
    content (Any): The content to be written within the file
  
  Returns:
    bool: indicates if writing json was successful or not
  """

  # Get directory name from output file path parameter value
  output_directory = os.path.dirname(output_file_path)

  # If the directory does not exist, create it
  if output_directory and not os.path.exists(output_directory):
    os.makedirs(output_directory)

  # Try writing content to the file - return True if all successful, otherwise catch the error, log and return False
  try:
    with open(output_file_path, "w") as output_file:
      json.dump(content, output_file, indent=4)

    print("Successfully saved content to {}".format(output_file_path))

    return True
  except(OSError, IOError) as e:
    print("Error saving content to {}".format(output_file_path))
    return False


def get_file_paths_matching_regex(directory, regex_pattern):
  """
  Get files within provided directory that match provided regex pattern

  Args:
    directory (str): path to search files
    regex_pattern: pattern to match each file name against
  """
  

  # Initialise empty dict
  unique_files_dict = {}
  
  # Loop over directory, check each file. If match for regex, set in dict, otherwise continue
  for root, dirs, files in os.walk(directory):
    for file_name in files:
      if re.search(regex_pattern, file_name):
        full_path = os.path.join(root, file_name)

        unique_files_dict[file_name] = full_path
  
  # Get list of dict values (i.e. file paths for which the regex matched)
  unique_files = list(unique_files_dict.values())
  
  # Return this list
  return unique_files


# Get RAG results files within inputs directory (NOTE: for this to work, files manually need to be placed there - whatever results we want to run DeepEval on)
rag_results_file_paths = get_file_paths_matching_regex("./inputs", r"(?=.*golden_results)(?=.*rag)")

# Initialise different deep eval metrics
contextual_precision = ContextualPrecisionMetric(async_mode=False)
contextual_recall = ContextualRecallMetric(async_mode=False)
contextual_relevancy = ContextualRelevancyMetric(async_mode=False)
answer_relevancy = AnswerRelevancyMetric(async_mode=False)
faithfulness = FaithfulnessMetric(truths_extraction_limit=50, async_mode=False)

# Loop over all files
for file_path in rag_results_file_paths:
  # For each result file (each being an individual hyperparameter confiuration run against the full golden dataset)
  # Initialise an empty list
  deep_eval_test_cases = []

  # Extract the results data
  current_result_info = read_json_file(file_path)
  
  # Loop over results within the individual file
  for i, info in enumerate(current_result_info["results"]):

    # Append to deep eval question list (note this is getting inputs into expected format by DeepEval)
    deep_eval_test_cases.append(LLMTestCase(
      input=info["question"],
      actual_output=info["answer"],
      expected_output=info["ground_truth"],
      retrieval_context=info["final_documents"]))
  
  # Initialise batch size (default had been 20, silently failed on GPUs on Colab with no indication memory constraints were the issue)
  BATCH_SIZE = 1

  # Initialise empty array for results
  file_results = []
  
  # Retry constant and timeout constants, again these were attempts to resolve on GPU but turned out memory constraints were the main bottleneck
  MAX_RETRIES = 3
  TIMEOUT = 180
  
  # Loop over the inputs for DeepEval
  for batch in chunked(deep_eval_test_cases, BATCH_SIZE):
    attempt = 0
    while attempt < MAX_RETRIES:
        # This concurrency functionality was really focused for cases where these tests would be batched
        # However, as mentioned above, this was only functional when cases were tested one at a time
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Note here, only one metric configured (I manually swapped these out between runs)
            # Once again, only worked when ran with individual metric, running with more than one metric configured
            # resulted in out-of-memory issues
            future = executor.submit(evaluate, batch, metrics=[answer_relevancy], async_config=AsyncConfig(run_async=False))
            try:
                result = future.result(timeout=TIMEOUT)
                # Append the raw DeepEval results to the file results list
                file_results.append(result.dict())
                break
            except concurrent.futures.TimeoutError:
                attempt += 1
                print(f"Batch timed out! Attempt {attempt} of {MAX_RETRIES}. Retrying in 5 seconds...")
                time.sleep(5)
    else:
        print("Batch failed after maximum retries.")
        file_results.append({"error": "timeout after retries"})
  
  # Once all files have been evaluated, generated unique timestamp for output file
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

  # Write contents to file
  write_json_file("{}/{}_qa_a_relevancy_quantised.json".format(".", timestamp), {"deepEval": file_results, "file_info": current_result_info})




