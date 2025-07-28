import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import numpy as np

def extract_contextual_relevancy_scores(target_metric):
    """
    Extract Contextual Relevancy scores from all JSON files

    Args:
        target_metric (str): which metric to extract
    """

    data = []
    
    # Get all JSON files in root directory (excluding .deepeval directory)
    json_files = [f for f in os.listdir(".") if f.endswith(".json") and not f.startswith(".")]

    # Initialise empty list for filtered contents
    filtered_file_contents = []
    
    # Loop over files
    for filename in json_files:
        try:
            # Read the file contents
            with open(filename, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            # Extract hyperparameters from file_info
            # Then extract max new tokens from hyperparameters, if not avaialble set to "unknown"
            file_info = content.get("file_info", {})
            hyperparameters = file_info.get("hyperparameters", {})
            max_tokens = hyperparameters.get("max_new_tokens", "unknown")
            
            # Extract timestamp from filename
            timestamp_match = re.search(r'(\d{8}_\d{6})', filename)
            timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
            
            # Get deepEval results
            deep_eval_results = content.get("deepEval", [])

            # Loop over results
            for _, individual_test_case in enumerate(deep_eval_results):
                # Get current iteration test information
                individual_test_info = individual_test_case.get("test_results")

                # loop over evaluated metrics list - if match found, append current file contents to list
                for _, item in enumerate(individual_test_info):
                    if item.get("metrics_data", [])[0].get("name", "") == target_metric:
                        filtered_file_contents.append(content)
                        break
                break
        
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    # Return filtered documents
    return filtered_file_contents


def create_hyperparam_id(hyperparameters):
    """
    Create a formatted string identifier for hyperparameters - used in graphs
    """

    # Define the order and format for each hyperparameter
    param_formats = {
        "max_new_tokens": "max{}",
        "temperature": "temp{}",
        "top_p": "topP{}",
        "top_k": "topK{}",
        "repetition_penalty": "repPen{}",
        "do_sample": "doSample{}",
        "num_beams": "beams{}",
        "length_penalty": "lenPen{}",
        "no_repeat_ngram_size": "noRep{}"
    }
    
    # Build the identifier string
    parts = []

    # Construct list with matched hyperparameters
    for param_name, format_str in param_formats.items():
        if param_name in hyperparameters:
            value = hyperparameters[param_name]
            # Format boolean values
            if isinstance(value, bool):
                value = "T" if value else "F"
            # Format float values to 2 decimal places
            elif isinstance(value, float):
                value = f"{value:.2f}".rstrip("0").rstrip(".")
            parts.append(format_str.format(value))
    
    # Return string representation which can be used in graphs to show hyperparam configs
    return "_".join(parts) if parts else "default"


def plot_bar_comparison(data, metric_type):
    """
    This function plots bar charts comparing results for provided metric_type parameter
    """

    # Initialise empty list
    results = []

    # Loop over data
    for i, item in enumerate(data):

        # For each, get the key information needed for plotting
        file_info = item.get("file_info", {})
        hyperparameters = file_info.get("hyperparameters", {})

        max_tokens = hyperparameters.get("max_new_tokens", "unknown")
        temperature = hyperparameters.get("temperature", "unknown")
        top_p = hyperparameters.get("top_p", "unknown")

        # Call utility function to generate string for hyperparameters
        # so that it can be used on graph
        hyperparam_id = create_hyperparam_id(hyperparameters)

        # Now extract the deepEval results
        deep_eval_results = item.get("deepEval", [])

        # Loop over results
        for j, test_item in enumerate(deep_eval_results):
            test_item_details = test_item["test_results"][0]

            # Get deep eval metric data
            metric_data = test_item_details["metrics_data"]

            # Get both the metric name and score
            metric_name = metric_data[0].get("name", "")
            score = metric_data[0].get("score", 0)

            # Append results to list
            results.append({
                    "hyperparam_id": hyperparam_id,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "question_index": j,
                    "metric_name": metric_name,
                    "score": score,
                    "question": test_item_details.get("input", f"Question_{j}"),
                    "file_index": i
                })

                
    # Construct dataframe from above results list
    df = pd.DataFrame(results)

    df.head()

    # Initialise figure size
    plt.figure(figsize=(12, 8))
    
    unique_configs = df["hyperparam_id"].unique()
    
    config_means = []
    config_names = []
    
    # Calculate mean score for each hyperparameter configuration file across all deepeval results
    for config in df["hyperparam_id"].unique():
        subset = df[df["hyperparam_id"] == config]
        mean_score = subset["score"].mean()
        config_means.append(mean_score)
        config_names.append(config)
        print(f"{config}: {len(subset)} points, mean score: {mean_score:.3f}")
    
    # Create bar plot
    plt.figure(figsize=(12, 8))
    
    # Create bars with same target hex code of "#198576"
    # with hyperparameter configurations and mean result values for the given metric
    bars = plt.bar(config_names, config_means, color=["#198576"], alpha=0.8)
    
    # Add value labels on top of bars
    for bar, mean_score in zip(bars, config_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{mean_score:.3f}', ha="center", va="bottom", fontweight="bold")
    
    # Add title, labels, etc, save figure using metric name in generated output name to ensure easy identification when extracting
    plt.xlabel("Hyperparameter Configuration")
    plt.ylabel("{} Mean Score".format(metric_type))
    plt.title("{} Mean Scores by Hyperparameter Configuration".format(metric_type))
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("hyperparameter_scatter_{}.png".format(metric_type.lower().replace(" ", "_")), dpi=300, bbox_inches="tight")
            


# Use the extract_contextual_relevancy_scores utility function to filter by given metric
context_relevancy_files = extract_contextual_relevancy_scores("Contextual Relevancy")
context_recall_files = extract_contextual_relevancy_scores("Contextual Recall")
context_precision_files = extract_contextual_relevancy_scores("Contextual Precision")
faithfulness_files = extract_contextual_relevancy_scores("Faithfulness")
a_relevancy_files = extract_contextual_relevancy_scores("Answer Relevancy")


# Then plot each to enable comparison across hyperparameter configurations for each DeepEval metric evaluated
plot_bar_comparison(context_relevancy_files, "Contextual Relevancy")
plot_bar_comparison(context_recall_files, "Contextual Recall")
plot_bar_comparison(context_precision_files, "Contextual Precision")
plot_bar_comparison(faithfulness_files , "Faithfulness")
plot_bar_comparison(a_relevancy_files , "Answer Relevancy")





        