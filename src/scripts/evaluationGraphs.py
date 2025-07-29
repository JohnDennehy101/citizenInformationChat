from pathlib import Path
from typing import List, Dict, Any
from statistics import mean, median, stdev
from collections import Counter
import matplotlib.pyplot as plt
import os
import json
import numpy as np

"""
This script was used to generate evaluation graphs for the thesis
Actual results of these can be found within data/graphs directory
"""

### Re-usable variables
GREEN_DARK = "#198576"
GREEN_LIGHT = "#abd6d0"

###### START OF UTILITY FUNCTIONS

def fix_nested_json_evaluation_files(target_path: str):
    """
    This function was required to standardise results files
    Some had a list structure (which is final target structure), others had dict with list within that key
    This function flattens any files that have that initial dict and move results into a list structure

    Args:
        target_path (str): where the input files are present that need to be sanitised
    """

    # Loop over all json files
    for file_path in Path(target_path).rglob("*.json"):
        # Open the file contents
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # If the data is a dict and it is single key, it is in incorrect format
            if isinstance(data, dict) and len(data) == 1:
                # Get the first key
                key = list(data.keys())[0]

                # The keys were storing the file name for the results so should contain / as ran on Mac
                if "/" in key or "\\" in key:
                    # Get the actual results
                    actual_content = data[key]
                
                # Then write that flattened structure back to the file, overwriting the incorrect format
                with open(file_path, "w") as f:
                    json.dump(actual_content, f, indent=4)
                
                # Some output to validate what is going on
                print("Fixed: {}".format(file_path))
        
        # If any error, print out to enable visual identification
        except (json.JSONDecodeError, Exception) as e:
            print("Error processing {}: {}".format(file_path, e))


def read_all_json_files_as_list(results_dir: str = "results") -> List[Dict[str, Any]]:
    """
    This function is called after the one above, to ensure that all retrieved documents are in expected format

    Args:
        results_dir (str): where to read the results files from
    """

    # Initialise empty list
    json_data_list = []

    # Get target directory
    results_path = Path(results_dir)
    
    # Return empty list if not a valid directory
    if not results_path.exists():
        print("Results directory '{}' does not exist.".format(results_dir))
        return json_data_list
    
    # Traverse the directory
    for root, dirs, files in os.walk(results_path):
        # Loop over files
        for file in files:
            # If json file, it is one we want to use
            if file.endswith(".json"):
                file_path = Path(root) / file
                try:
                    # Read the json file, append to list
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    json_data_list.append({
                        "file_path": str(file_path),
                        "data": data
                    })
                    print("Successfully loaded: {}".format(file_path))
                except json.JSONDecodeError as e:
                    print("Error parsing JSON in {}: {}".format(file_path, e))
                except Exception as e:
                    print("Error reading {}: {}".format(file_path, e))
    
    # Final validation informing user how many files were extracted
    print("\nTotal JSON files loaded: {}".format(len(json_data_list)))

    # Return the contents
    return json_data_list

def add_type_property_to_result_files(all_results):
    """
    Initially, whether result file was RAG or LLM was only identifiable by file name
    This function adds a property to the results file to add type of RAG or LLM for easier comparison

    Args:
        all_results: list of results files
    """

    # Loop over all results passed
    for file_info in all_results:
        # Extract the properties
        file_path = file_info["file_path"]
        data = file_info["data"]

        # Simple check, if "rag" or "llm" in file name
        # set variable value
        if "rag" in file_path.lower():
            type_value = "rag"
        elif "llm" in file_path.lower():
            type_value = "llm"
        
        # Set type property value
        data["type"] = type_value

        # Write updated content back to file (note new type prop now has "rag" or "llm")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print("Updated: {}".format(file_path))
        except Exception as e:
            print("Error writing to {}: {}".format(file_path, e))

def compute_performance_by_type(all_results, metric_name: str, operation: str, type_filter=None):
    """
    Compute metrics performance by metric and operation name

    Args:
        all_results: all results that have been parsed from json files
        metric_name (str): target metric to compute performance metric operation
        operation (str): what operation is target (i.e. mean, min, max)
        type_filter (str): defaults to none, can be set to filter by type (e.g. rag , llm)
    """

    # Define operations dict
    operations = {
        "mean": lambda x: mean(x),
        "median": lambda x: median(x),
        "min": lambda x: min(x),
        "max": lambda x: max(x),
        "std": lambda x: stdev(x) if len(x) > 1 else 0,
        "label_counts": lambda x: dict(Counter(x)),
        "avg_entailment_prob": lambda x: mean([prob_dict["entailment"] for prob_dict in x]),
        "avg_contradiction_prob": lambda x: mean([prob_dict["contradiction"] for prob_dict in x]),
        "avg_neutral_prob": lambda x: mean([prob_dict["neutral"] for prob_dict in x]),
    }

    metric_values = []
    filtered_files = []

    # Loop over files
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # If type filter matches property in file (e.g. "rag")
        if type_filter != None and "type" in data and data["type"] == type_filter:
            # Append to filtered files
            filtered_files.append(file_info)

            # Next check if target metric available
            if "metrics" in data and metric_name in data["metrics"]:
                # If so extract metric data
                metric_data = data["metrics"][metric_name]
                # If valid operation, compute operation metric score and append
                if operation in metric_data:
                    metric_values.append(metric_data[operation])
        
        # If filter type is None, then compute for all files
        elif type_filter == None:
            filtered_files.append(file_info)
            if "metrics" in data and metric_name in data["metrics"]:
                metric_data = data["metrics"][metric_name]
                if operation in metric_data:
                    metric_values.append(metric_data[operation])
    
    # If no metric results found, return early and inform with print statement
    if len(metric_values) < 1:
        print("No values found for metric: {}".format(metric_name))
        return None
    
    # If invalid operation, return early and inform with print statement
    if operation not in operations:
        print("Unknown operation: {}. Available: {}".format(operation, list(operations.keys())))
        return None
    
    # Extract computed score for target operation and metric
    computed_value = operations[operation](metric_values)

    # Return dict with the relevant information
    return {
        "metric_name": metric_name,
        "operation": operation,
        "computed_value": computed_value,
        "total_files": len(metric_values),
        "files_processed": len(filtered_files),
        "metric_values": metric_values
    }

def compare_performance_by_type(all_results, metric_name: str, operation: str):
    """
    This function enables comparison between RAG and LLM model runs for a given metric name and operation type

    Args:
        all_results: results that have been parsed from json files
        metric_name (str): the metric name for which performance should be compared
        operation (str): what operation is the target (i.e. mean, min, max etc)
    """

    # Call utility function to get performance metrics for metric name, operation type
    # First one computes across both llm and rag runs

    # Then 2nd & 3rd filter to individual experiment type to enable direct comparison between RAG & LLM
    all_performance = compute_performance_by_type(all_results, metric_name, operation)
    rag_performance = compute_performance_by_type(all_results, metric_name, operation, "rag")
    llm_performance = compute_performance_by_type(all_results, metric_name, operation, "llm")

    # Extract computed scores for rag and llm for the given metric and operation
    rag_value = rag_performance["computed_value"]
    llm_value = llm_performance["computed_value"]

    # Return dict with comparison score between the methods
    # Also return overall performance across runs to enable comparison there as well
    comparison = {
        "metric_name": metric_name,
        "operation": operation,
        "overall": all_performance,
        "rag": rag_performance,
        "llm": llm_performance,
        "difference": {
            "rag_minus_llm": rag_value - llm_value,
            "llm_minus_rag": llm_value - rag_value,
            "percentage_diff": abs((rag_value - llm_value) / llm_value * 100) if llm_value != 0 else float("inf")
        }
    }

    return comparison


def simple_comparison_plot(value1: float, value2: float, 
                          label1: str = "Method 1", 
                          label2: str = "Method 2",
                          title: str = "Comparison",
                          ylabel: str = "Score",
                          save_path: str = "comparison_plot.png",
                          higher_is_better: bool = True) -> None:
    """
    Simple bar plot comparing two values and save to target file at provided save path after generation

    Args:
        value1: first value to be plotted on left bar
        value2: second value which is plotted on right bar
        label1: first label to be associated with left plot
        label2: second label to be associated with right plot
    """

    fig, ax = plt.subplots(figsize=(8, 6))
    
    methods = [label1, label2]
    values = [value1, value2]
    
    # Define colours to be used in graph
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT
    
    # Determine colours to use based on which value is better
    if higher_is_better:
        colours = [green_dark if value1 >= value2 else green_light, 
                  green_dark if value2 >= value1 else green_light]
    else:
        colours = [green_dark if value1 <= value2 else green_light, 
                  green_dark if value2 <= value1 else green_light]
    
    # Bar chart
    bars = ax.bar(methods, values, color=colours, alpha=0.8)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        y_pos = height + (max(values) * 0.02)
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{value:.4f}', ha="center", va="bottom", fontweight="bold")
    
    # Metadata for plot
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    
    # Save the graph to provided save_path parameter
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_label_distributions(all_results: List[Dict[str, Any]], 
                               filter_type: str = None) -> Dict[str, Any]:
    """
    Compare label distributions between RAG and LLM. This is the zero-shot classification task for the LLM as a judge model.
    
    Args:
        all_results: List of result dictionaries
        filter_type: Type to filter by ("rag", "llm", or None for all)
    
    Returns:
        Dictionary with label distribution comparison
    """

    # Initialise empty lists for both rag and llm
    rag_labels = []
    llm_labels = []
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Check if we should include this file based on type filter
        if filter_type is not None:
            file_type = data.get("type", "unknown")
            if file_type != filter_type:
                continue
        
        # Get the pre-computed label counts and filter based on rag  / llm
        if "metrics" in data and "zero_shot_label" in data["metrics"]:
            label_data = data["metrics"]["zero_shot_label"]
            if "label_counts" in label_data:
                label_counts = label_data["label_counts"]
                
                # Determine if this is RAG or LLM based on file path or type
                file_type = data.get("type", "unknown")
                if "rag" in file_path.lower() or file_type == "rag":
                    rag_labels.append(label_counts)
                elif "llm" in file_path.lower() or file_type == "llm":
                    llm_labels.append(label_counts)
    
    # Aggregate counts utility function to extract counts per label ("Entailment", "Neutral", "Contradiction")
    def aggregate_counts(label_list):
        total_counts = {}
        for counts in label_list:
            for label, count in counts.items():
                total_counts[label] = total_counts.get(label, 0) + count
        return total_counts
    
    # Get counts for zero shot labelling for rag and llm separately
    rag_total = aggregate_counts(rag_labels)
    llm_total = aggregate_counts(llm_labels)
    
    # Return these to enable plotting
    return {
        "rag_labels": rag_total,
        "llm_labels": llm_total,
        "rag_files": len(rag_labels),
        "llm_files": len(llm_labels)
    }

def plot_label_comparison(all_results: List[Dict[str, Any]], 
                         save_path: str = "label_comparison.png") -> None:
    """
    Create a bar plot comparing label distributions for zero shot labelling task with LLM as a judge

    Args:
        all_results: again, these have been extracted from json files
        save_path (str): where to save the generated graph
    """

    # Call utility function above to get LLM as a judge zero shot labelling results per method
    comparison = compare_label_distributions(all_results)
    
    # Extract RAG and LLM results into separate variables
    rag_labels = comparison["rag_labels"]
    llm_labels = comparison["llm_labels"]
    
    # Get all unique labels
    all_labels = set(rag_labels.keys()) | set(llm_labels.keys())
    
    # Prepare data for plotting
    labels = list(all_labels)
    rag_values = [rag_labels.get(label, 0) for label in labels]
    llm_values = [llm_labels.get(label, 0) for label in labels]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(labels))
    width = 0.35

    # Use variables to keep styling constant
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT
    
    # Using bars makes it easy visually to compare between the two
    bars1 = ax.bar(x - width/2, rag_values, width, label="RAG", color=green_dark, alpha=0.8)
    bars2 = ax.bar(x + width/2, llm_values, width, label="LLM", color=green_light, alpha=0.8)
    
    ax.set_xlabel("Labels")
    ax.set_ylabel("Count")
    ax.set_title("Zero-Shot Label Distribution Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha="center", va="bottom", fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_label_pie_charts(all_results: List[Dict[str, Any]], 
                         save_path: str = "label_pie_charts.png") -> None:
    """
    Create pie charts comparing label distributions for RAG and LLM.

    Args:
        all_results: again, these have been extracted from json files
        save_path (str): where to save the generated graph
    """

    # Again extract zero-shot labelling results
    comparison = compare_label_distributions(all_results)
    
    rag_labels = comparison["rag_labels"]
    llm_labels = comparison["llm_labels"]
    
    # Green Colours for the labels
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT

    
    colours = [green_light, green_dark, "#45B7D1"]
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # RAG Pie Chart
    rag_values = list(rag_labels.values())
    rag_keys = list(rag_labels.keys())
    
    wedges1, texts1, autotexts1 = ax1.pie(rag_values, labels=rag_keys, autopct='%1.1f%%', 
                                         colors=colours, startangle=90)
    ax1.set_title("RAG Label Distribution", fontsize=14, fontweight="bold")
    
    # LLM Pie Chart
    llm_values = list(llm_labels.values())
    llm_keys = list(llm_labels.keys())
    
    wedges2, texts2, autotexts2 = ax2.pie(llm_values, labels=llm_keys, autopct='%1.1f%%', 
                                         colors=colours, startangle=90)
    ax2.set_title("LLM Label Distribution", fontsize=14, fontweight="bold")
    
    # Add total counts as text for an easy comparison
    ax1.text(0, -1.2, f'Total: {sum(rag_values):,}', ha="center", va="center", 
             fontsize=12, fontweight="bold")
    ax2.text(0, -1.2, f'Total: {sum(llm_values):,}', ha="center", va="center", 
             fontsize=12, fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_probability_distributions(all_results: List[Dict[str, Any]], 
                                     filter_type: str = None) -> Dict[str, Any]:
    """
    Compare probability distributions between RAG and LLM.
    
    Args:
        all_results: List of result dictionaries
        filter_type: Type to filter by ("rag", "llm", or None for all)
    
    Returns:
        Dictionary with probability distribution comparison
    """
    rag_probs = []
    llm_probs = []
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Check if we should include this file based on type filter
        if filter_type is not None:
            file_type = data.get("type", "unknown")
            # Continue to next iteration if current file is not of correct filter type
            if file_type != filter_type:
                continue
        
        # Get the probability averages
        if "metrics" in data and "zero_shot_probabilities" in data["metrics"]:
            prob_data = data["metrics"]["zero_shot_probabilities"]
            
            # Determine if this is RAG or LLM based on file path or type
            file_type = data.get("type", "unknown")
            if "rag" in file_path.lower() or file_type == "rag":
                rag_probs.append(prob_data)
            elif "llm" in file_path.lower() or file_type == "llm":
                llm_probs.append(prob_data)
    
    # Calculate averages across all files - function defined inline as only used here
    def average_probabilities(prob_list):
        if not prob_list:
            return {}
        
        total_probs = {}
        for probs in prob_list:
            for prob_type, value in probs.items():
                if prob_type not in total_probs:
                    total_probs[prob_type] = []
                total_probs[prob_type].append(value)
        
        # Calculate mean for each probability type
        avg_probs = {}
        for prob_type, values in total_probs.items():
            avg_probs[prob_type] = mean(values)
        
        return avg_probs
    
    # Call inline function to generate mean rag and llm performance
    rag_avg = average_probabilities(rag_probs)
    llm_avg = average_probabilities(llm_probs)
    
    return {
        "rag_probabilities": rag_avg,
        "llm_probabilities": llm_avg,
        "rag_files": len(rag_probs),
        "llm_files": len(llm_probs)
    }

def plot_probability_comparison(all_results: List[Dict[str, Any]], 
                               save_path: str = "probability_comparison.png") -> None:
    """
    Create bar plots comparing probability distributions.

    Args:
        all_results: again, these have been extracted from json files
        save_path (str): where to save the generated graph
    """
    comparison = compare_probability_distributions(all_results)
    
    rag_probs = comparison["rag_probabilities"]
    llm_probs = comparison["llm_probabilities"]
    
    # Get probability types
    prob_types = list(rag_probs.keys())
    
    # Prepare data for plotting
    rag_values = [rag_probs[prob_type] for prob_type in prob_types]
    llm_values = [llm_probs[prob_type] for prob_type in prob_types]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(prob_types))
    width = 0.35
    
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT
    
    # Compute bar value config values
    bars1 = ax.bar(x - width/2, rag_values, width, label="RAG", color=green_dark, alpha=0.8)
    bars2 = ax.bar(x + width/2, llm_values, width, label="LLM", color=green_light, alpha=0.8)
    
    ax.set_xlabel("Probability Types")
    ax.set_ylabel("Average Probability")
    ax.set_title("Zero-Shot Probability Distribution Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels([pt.replace("avg_", "").replace("_prob", "").title() for pt in prob_types])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.3f}', ha="center", va="bottom", fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_performance_by_model(all_results: List[Dict[str, Any]], 
                                metric_name: str,
                                operation: str = "mean") -> Dict[str, Any]:
    """
    Compare performance across different models for a given metric and operation type
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to compare
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
    
    Returns:
        Dictionary with model comparison results
    """
    model_performance = {}
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Get the pre-computed metric value
        if "metrics" in data and metric_name in data["metrics"]:
            metric_data = data["metrics"][metric_name]
            if operation in metric_data:
                metric_value = metric_data[operation]
                # Extract model name from the data
                model_name = data.get("model", "unknown")
                
                if model_name and model_name != "unknown":
                    if model_name not in model_performance:
                        model_performance[model_name] = []
                    model_performance[model_name].append(metric_value)
        else:
            continue
    
    # Calculate statistics for each model (note lots of different operations for rich comparison)
    model_stats = {}
    for model, values in model_performance.items():
        if values:
            model_stats[model] = {
                "mean": mean(values),
                "min": min(values),
                "max": max(values),
                "std": stdev(values) if len(values) > 1 else 0,
                "count": len(values),
                "values": values
            }
    
    return {
        "metric_name": metric_name,
        "operation": operation,
        "model_performance": model_stats
    }

def plot_model_comparison_by_type(all_results: List[Dict[str, Any]], 
                                 metric_name: str,
                                 operation: str = "mean",
                                 save_path: str = "model_comparison_by_type.png",
                                 min_count: int = 5) -> None:
    """
    Create separate bar plots comparing performance across models for RAG and LLM.

    Args:
        all_results: again, these have been extracted from json files
        metric_name (str): target metric for which model should be compared
        operation (str): defaults to mean, other operations such as min, max are also supported
        save_path (str): where to save the generated graph
        min_count (int): this is to ensure that solitary experiments can be excluded (e.g. fine-tuning was far less prevalent than RAG vs LLM)
    """
    # Split by type
    rag_results = [r for r in all_results if r["data"].get("type") == "rag"]
    llm_results = [r for r in all_results if r["data"].get("type") == "llm"]
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # RAG comparison
    rag_comparison = compare_performance_by_model(rag_results, metric_name, operation)
    rag_stats = rag_comparison["model_performance"]

    # Note filter here as fine-tuned model only had one run so was skewing results
    rag_stats_filtered = {k: v for k, v in rag_stats.items() if v["count"] > min_count}
    
    # If filtered results available extract values and plot graph, note formatting for RAG model names
    if rag_stats_filtered:
        rag_models = list(rag_stats_filtered.keys())
        rag_means = [rag_stats_filtered[model][operation] for model in rag_models]

        rag_models_short = [model.split("/")[-1] if "/" in model else model for model in rag_models]
        
        bars1 = ax1.bar(rag_models_short, rag_means, color=GREEN_DARK, alpha=0.8)
        ax1.set_title(f"RAG Models - {metric_name.upper()} ({operation.upper()})")
        ax1.set_ylabel("Score")
        ax1.tick_params(axis="x", rotation=45)
        ax1.grid(axis="y", alpha=0.3)
        
        # Add value labels
        for bar, mean_val in zip(bars1, rag_means):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{mean_val:.4f}', ha="center", va="bottom", fontweight="bold")
    
    # LLM comparison
    llm_comparison = compare_performance_by_model(llm_results, metric_name, operation)
    llm_stats = llm_comparison["model_performance"]
    
    # Apply min_count filter to LLM as well
    llm_stats_filtered = {k: v for k, v in llm_stats.items() if v["count"] > min_count}
    
    if llm_stats_filtered:
        llm_models = list(llm_stats_filtered.keys())
        llm_means = [llm_stats_filtered[model][operation] for model in llm_models]

        llm_models_short = [model.split("/")[-1] if "/" in model else model for model in llm_models]
        
        bars2 = ax2.bar(llm_models_short, llm_means, color=GREEN_LIGHT, alpha=0.8)
        ax2.set_title(f"LLM Models - {metric_name.upper()} ({operation.upper()})")
        ax2.set_ylabel("Score")
        ax2.tick_params(axis="x", rotation=45)
        ax2.grid(axis="y", alpha=0.3)
        
        # Add value labels
        for bar, mean_val in zip(bars2, llm_means):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{mean_val:.4f}', ha="center", va="bottom", fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_file_distribution_pie(all_results: List[Dict[str, Any]], 
                              save_path: str = "file_distribution_pie.png") -> None:
    """
    Create a pie chart showing the distribution of RAG vs LLM files.

    Args:
        all_results: again, these have been extracted from json files
        save_path (str): where to save the generated graph
    """
    # Count files by type
    rag_count = 0
    llm_count = 0
    
    for file_info in all_results:
        file_type = file_info["data"].get("type", "unknown")
        if file_type == "rag":
            rag_count += 1
        elif file_type == "llm":
            llm_count += 1
    
    # Prepare data for pie chart
    labels = ["RAG", "LLM"]
    sizes = [rag_count, llm_count]
    colours = [GREEN_DARK, GREEN_LIGHT]
    
    # Create the pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                     colors=colours, startangle=90)
    
    ax.set_title("File Distribution: RAG vs LLM", fontsize=14, fontweight="bold")
    
    # Add total count as text
    total_files = rag_count + llm_count
    ax.text(0, -1.2, f"Total Files: {total_files}", ha="center", va="center", 
            fontsize=12, fontweight="bold")
    
    # Add individual counts
    ax.text(-0.8, 0.5, f"RAG: {rag_count}", ha="center", va="center", fontsize=10)
    ax.text(0.8, 0.5, f"LLM: {llm_count}", ha="center", va="center", fontsize=10)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def get_top_performing_configs(all_results: List[Dict[str, Any]], 
                              metric_name: str,
                              operation: str = "mean",
                              top_n: int = 10,
                              filter_type: str = None) -> List[Dict[str, Any]]:
    """
    Get the top N performing hyperparameter configurations for a given metric.
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to rank by
        operation: Operation to use ("mean", "min", "max", "median", "std", "count")
        top_n: Number of top configurations to return
        filter_type: Type to filter by ("rag", "llm", or None for all)
    
    Returns:
        List of top performing configurations with their details
    """
    configs = []
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Check if we should include this file based on type filter
        if filter_type is not None:
            file_type = data.get("type", "unknown")
            if file_type != filter_type:
                continue
        
        # Get the pre-computed metric value
        if "metrics" in data and metric_name in data["metrics"]:
            metric_data = data["metrics"][metric_name]
            if operation in metric_data:
                metric_value = metric_data[operation]
                
                # Extract configuration details
                config_info = {
                    "file_path": file_path,
                    "metric_value": metric_value,
                    "type": data.get("type", "unknown"),
                    "model": data.get("model", "unknown"),
                    "hyperparameters": data.get("hyperparameters", {})
                }
                
                configs.append(config_info)
    
    # Sort by metric value (descending for higher-is-better metrics)
    configs.sort(key=lambda x: x["metric_value"], reverse=True)
    
    # Return top N configs
    return configs[:top_n]

def plot_top_configs_with_hyperparams(all_results: List[Dict[str, Any]], 
                                     metric_name: str,
                                     operation: str = "mean",
                                     top_n: int = 10,
                                     filter_type: str = None,
                                     save_path: str = "top_configs_with_hyperparams.png") -> None:
    """
    Create a horizontal bar plot showing top hyperparameter configurations with hyperparameters.

    Args:
        all_results: again, these have been extracted from json files
        metric_name (str): what evalaution metric should be used for analysis
        operation (str): what calculation should be undertaken
        top_n (int): how many hyperparameter configs to return
        filter_type (str): if None, all experiments used. Can filter by "rag" or "llm"
        save_path (str): where to save the generated graph
    """

    top_configs = get_top_performing_configs(all_results, metric_name, operation, top_n, filter_type)
    
    if not top_configs:
        print(f"No configurations found for {metric_name}")
        return
    
    # Initialise empty lists
    config_labels = []
    metric_values = []
    colours = []
    
    for i, config in enumerate(top_configs):
        # Create a detailed label with hyperparameters
        model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
        config_type = config["type"]
        
        # Format hyperparameters
        hyperparams = config["hyperparameters"]
        if hyperparams:
            # Create a compact hyperparameter string
            hp_parts = []
            for key, value in hyperparams.items():
                # Set key value which will be easy to identify on graph
                if isinstance(value, (int, float)):
                    hp_parts.append(f"{key}={value}")
                # Truncate long strings to avoid overflowing graph
                else:
                    hp_parts.append(f"{key}={str(value)[:10]}...")
            
            # Set to string type
            hp_str = ", ".join(hp_parts)
            label = f"{i+1}. {config_type} - {model}\n   {hp_str}"
        else:
            label = f"{i+1}. {config_type} - {model}\n   (no hyperparameters)"
        
        config_labels.append(label)
        metric_values.append(config["metric_value"])
        
        # Colour based on type
        colours.append(GREEN_DARK if config_type == "rag" else GREEN_LIGHT)
    
    # Create the plot with more height for longer labels
    fig, ax = plt.subplots(figsize=(12, max(8, top_n * 0.6)))
    
    bars = ax.barh(config_labels, metric_values, color=colours, alpha=0.8)
    
    ax.set_xlabel(f"{metric_name.upper()} Score")
    ax.set_title(f"Top {top_n} Configurations - {metric_name.upper()} ({operation.upper()})")
    ax.grid(axis="x", alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, metric_values):
        width = bar.get_width()
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2,
               f"{value:.4f}", ha="left", va="bottom", fontweight="bold")
    
    # Save the graph with top hyperparameter configs
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def get_top_entailment_configs(all_results: List[Dict[str, Any]], 
                              top_n: int = 10,
                              filter_type: str = None) -> List[Dict[str, Any]]:
    """
    Get the top hyperparameter and model configurations with highest entailment counts.
    
    Args:
        all_results: List of result dictionaries
        top_n: Number of top configurations to return
        filter_type: Type to filter by ("rag", "llm", or None for all)
    
    Returns:
        List of top performing configurations with their details
    """
    configs = []
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Check if we should include this file based on type filter
        if filter_type is not None:
            file_type = data.get("type", "unknown")
            if file_type != filter_type:
                continue
        
        # Get the entailment count
        if "metrics" in data and "zero_shot_label" in data["metrics"]:
            label_data = data["metrics"]["zero_shot_label"]
            if "label_counts" in label_data:
                label_counts = label_data["label_counts"]
                entailment_count = label_counts.get("entailment", 0)
                
                # Extract configuration details
                config_info = {
                    "file_path": file_path,
                    "entailment_count": entailment_count,
                    "type": data.get("type", "unknown"),
                    "model": data.get("model", "unknown"),
                    "hyperparameters": data.get("hyperparameters", {}),
                    "label_counts": label_counts
                }
                
                # Extract hyperparameters from nested structure
                for key, value in data.items():
                    if isinstance(value, dict) and "hyperparameters" in value:
                        config_info["hyperparameters"] = value["hyperparameters"]
                        if "model" in value:
                            config_info["model"] = value["model"]
                        break
                
                configs.append(config_info)
    
    # Sort by entailment count (descending)
    configs.sort(key=lambda x: x["entailment_count"], reverse=True)
    
    # Return top N configurations based on entailment label counts
    return configs[:top_n]

def plot_top_entailment_configs(all_results: List[Dict[str, Any]], 
                               top_n: int = 10,
                               filter_type: str = None,
                               save_path: str = "top_entailment_configs.png") -> None:
    """
    Create a horizontal bar plot showing top configurations by entailment count.

    Args:
        all_results: again, these have been extracted from json files
        top_n: Number of top configurations to return
        filter_type: Type to filter by ("rag", "llm", or None for all)
        save_path (str): where to save the generated graph
    """

    # Call function above to get data in correct format for plotting
    top_configs = get_top_entailment_configs(all_results, top_n, filter_type)
    
    if not top_configs:
        print(f"No entailment data found")
        return
    
    # Prepare data for plotting
    config_labels = []
    entailment_counts = []
    colours = []
    
    for i, config in enumerate(top_configs):
        # Create a detailed label with hyperparameters
        model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
        config_type = config["type"]
        
        # Format hyperparameters
        hyperparams = config["hyperparameters"]
        if hyperparams:
            hp_parts = []
            for key, value in hyperparams.items():
                if isinstance(value, (int, float)):
                    hp_parts.append(f"{key}={value}")
                else:
                    hp_parts.append(f"{key}={str(value)[:10]}...")
            
            hp_str = ", ".join(hp_parts)
            label = f"{i+1}. {config_type} - {model}\n   {hp_str}"
        else:
            label = f"{i+1}. {config_type} - {model}\n   (no hyperparameters)"
        
        config_labels.append(label)
        entailment_counts.append(config["entailment_count"])
        
        # Colour based on type
        colours.append(GREEN_DARK if config_type == "rag" else GREEN_LIGHT)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, max(8, top_n * 0.6)))
    
    bars = ax.barh(config_labels, entailment_counts, color=colours, alpha=0.8)
    
    ax.set_xlabel("Entailment Count")
    ax.set_title(f"Top {top_n} Configurations by Entailment Count")
    ax.grid(axis="x", alpha=0.3)
    
    # Add value labels on bars
    for bar, count in zip(bars, entailment_counts):
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
               f"{count}", ha="left", va="center", fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_prompt_distribution_pie(all_results: List[Dict[str, Any]], 
                                save_path: str = "prompt_distribution_pie.png") -> None:
    """
    Create a pie chart showing the distribution of prompt types.

    Args:
        all_results: again, these have been extracted from json files
        save_path (str): where to save the generated graph
    """

    # Count files by prompt type
    prompt_counts = {}
    
    for file_info in all_results:
        data = file_info["data"]
        
        # Get prompt type from data
        prompt_type = data.get("prompt_type", "unknown")
        prompt_counts[prompt_type] = prompt_counts.get(prompt_type, 0) + 1
    
    if not prompt_counts:
        print("No prompt types found")
        return
    
    # Prepare data for pie chart
    labels = list(prompt_counts.keys())
    sizes = list(prompt_counts.values())
    
    # Create a colour palette for different prompt types
    colours = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    
    # Create the pie chart
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Don't show percentage in autopct, we'll add it manually
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct="", 
                                     colors=colours, startangle=90)
    
    ax.set_title("File Distribution by Prompt Type", fontsize=14, fontweight="bold")
    
    # Add total count as text
    total_files = sum(sizes)
    ax.text(0, -1.3, f"Total Files: {total_files}", ha="center", va="center", 
            fontsize=12, fontweight="bold")
    
    # Add percentage and count labels manually
    for i, (wedge, size) in enumerate(zip(wedges, sizes)):
        # Calculate percentage
        percentage = (size / total_files) * 100
        
        # Get the center angle of the wedge
        center_angle = wedge.theta1 + (wedge.theta2 - wedge.theta1) / 2
        
        # Add percentage at inner radius
        x_inner = 0.4 * np.cos(np.radians(center_angle))
        y_inner = 0.4 * np.sin(np.radians(center_angle))
        ax.text(x_inner, y_inner, f"{percentage:.1f}%", ha="center", va="center", 
                fontsize=10, fontweight="bold")
        
        # Add count at outer radius
        x_outer = 0.8 * np.cos(np.radians(center_angle))
        y_outer = 0.8 * np.sin(np.radians(center_angle))
        ax.text(x_outer, y_outer, f"{size}", ha="center", va="center", 
                fontsize=10, fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_performance_by_prompt_type(all_results: List[Dict[str, Any]], 
                                      metric_name: str,
                                      operation: str = "mean") -> Dict[str, Any]:
    """
    Compare performance across different prompt types.
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to compare
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
    
    Returns:
        Dictionary with prompt type comparison results
    """
    prompt_performance = {}
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Get the pre-computed metric value
        if "metrics" in data and metric_name in data["metrics"]:
            metric_data = data["metrics"][metric_name]
            if operation in metric_data:
                metric_value = metric_data[operation]
                
                # Get prompt type from data
                prompt_type = data.get("prompt_type", "unknown")
                
                if prompt_type not in prompt_performance:
                    prompt_performance[prompt_type] = []
                prompt_performance[prompt_type].append(metric_value)
    
    # Calculate statistics for each prompt type
    prompt_stats = {}
    for prompt_type, values in prompt_performance.items():
        if values:
            prompt_stats[prompt_type] = {
                "mean": mean(values),
                "min": min(values),
                "max": max(values),
                "std": stdev(values) if len(values) > 1 else 0,
                "count": len(values),
                "values": values
            }
    
    # Return data in format that is easy to plot
    return {
        "metric_name": metric_name,
        "operation": operation,
        "prompt_performance": prompt_stats
    }

def plot_prompt_comparison_simple(all_results: List[Dict[str, Any]], 
                                 metric_name: str,
                                 operation: str = "mean",
                                 filter_type: str = None,
                                 save_path: str = "prompt_comparison_simple.png") -> None:
    """
    Create a simple bar plot comparing performance across prompt types.
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to compare
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
        filter_type: Type to filter by ("rag", "llm", or None for all)
        save_path: Path to save the plot
    """
    # Filter by type if specified
    if filter_type is not None:
        filtered_results = [r for r in all_results if r["data"].get("type") == filter_type]
    else:
        filtered_results = all_results
    
    comparison = compare_performance_by_prompt_type(filtered_results, metric_name, operation)
    
    prompt_stats = comparison["prompt_performance"]
    
    if not prompt_stats:
        print(f"No data found for {metric_name}")
        return
    
    # Prepare data for plotting
    prompt_types = list(prompt_stats.keys())
    means = [prompt_stats[prompt_type][operation] for prompt_type in prompt_types]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use consistent colours
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT
    
    # Use single colur for all bars
    colours = [green_dark] * len(prompt_types)
    
    bars = ax.bar(prompt_types, means, color=colours, alpha=0.8)
    
    # Create title with filter info
    title = f"{metric_name.upper()} Comparison Across Prompt Types ({operation.upper()})"
    if filter_type:
        title += f" - {filter_type.upper()} Only"
    ax.set_title(title)
    
    ax.set_xlabel("Prompt Types")
    ax.set_ylabel("Score")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    
    # Add value labels on bars
    for bar, mean_val in zip(bars, means):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f"{mean_val:.4f}", ha="center", va="bottom", fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_reranking_impact(all_results: List[Dict[str, Any]], 
                            metric_name: str,
                            operation: str = "mean") -> Dict[str, Any]:
    """
    Compare performance between RAG with and without re-ranking.
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to compare
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
    
    Returns:
        Dictionary with re-ranking comparison results
    """

    rerank_performance = {}
    no_rerank_performance = {}
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Only process RAG files
        if data.get("type") != "rag":
            continue
        
        # Get the pre-computed metric value
        if "metrics" in data and metric_name in data["metrics"]:
            metric_data = data["metrics"][metric_name]
            if operation in metric_data:
                metric_value = metric_data[operation]
                
                # Check if re-ranking is used
                has_reranker = "reranker" in data and data["reranker"] is not None
                
                if has_reranker:
                    if "rerank" not in rerank_performance:
                        rerank_performance["rerank"] = []
                    rerank_performance["rerank"].append(metric_value)
                else:
                    if "no_rerank" not in no_rerank_performance:
                        no_rerank_performance["no_rerank"] = []
                    no_rerank_performance["no_rerank"].append(metric_value)
    
    # Calculate statistics
    def calculate_stats(performance_dict):
        stats = {}
        for key, values in performance_dict.items():
            if values:
                stats[key] = {
                    "mean": mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std": stdev(values) if len(values) > 1 else 0,
                    "count": len(values),
                    "values": values
                }
        return stats
    
    return {
        "metric_name": metric_name,
        "operation": operation,
        "rerank_stats": calculate_stats(rerank_performance),
        "no_rerank_stats": calculate_stats(no_rerank_performance)
    }

def plot_reranking_comparison(all_results: List[Dict[str, Any]], 
                             metric_name: str,
                             operation: str = "mean",
                             save_path: str = "reranking_comparison.png") -> None:
    """
    Create a bar plot comparing RAG performance with and without re-ranking.

    Args:
        all_results: again, these have been extracted from json files
        metric_name: Name of the metric to compare
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
        save_path (str): where to save the generated figure
    """
    comparison = compare_reranking_impact(all_results, metric_name, operation)
    
    rerank_stats = comparison["rerank_stats"]
    no_rerank_stats = comparison["no_rerank_stats"]
    
    if not rerank_stats and not no_rerank_stats:
        print(f"No re-ranking data found for {metric_name}")
        return
    
    # Prepare data for plotting
    labels = []
    values = []
    colours = []
    counts = []
    
    if "rerank" in rerank_stats:
        labels.append("With Re-ranking")
        values.append(rerank_stats["rerank"][operation])
        colours.append(GREEN_DARK)
        counts.append(rerank_stats["rerank"]["count"])
    
    if "no_rerank" in no_rerank_stats:
        labels.append("Without Re-ranking")
        values.append(no_rerank_stats["no_rerank"][operation])
        colours.append(GREEN_LIGHT)  
        counts.append(no_rerank_stats["no_rerank"]["count"])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    bars = ax.bar(labels, values, color=colours, alpha=0.8)
    
    ax.set_title(f"RAG Performance: {metric_name.upper()} ({operation.upper()})")
    ax.set_ylabel("Score")
    ax.grid(axis="y", alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f"{value:.4f}", ha="center", va="bottom", fontweight="bold")
    
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2., -0.02,
               f"n={count}", ha="center", va="top", fontweight="bold", fontsize=10,
               color="darkblue")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

def get_top_rag_configs_with_reranking(all_results: List[Dict[str, Any]], 
                                      metric_name: str,
                                      operation: str = "mean",
                                      top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Get top performing RAG configurations with reranking information and document counts.
    
    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to rank by
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
        top_n: Number of top configurations to return
    
    Returns:
        List of top configurations with reranking and document information
    """
    rag_configs = []
    
    for file_info in all_results:
        file_path = file_info["file_path"]
        data = file_info["data"]
        
        # Only process RAG files
        if data.get("type") != "rag":
            continue
        
        # Get the pre-computed metric value
        if "metrics" in data and metric_name in data["metrics"]:
            metric_data = data["metrics"][metric_name]
            if operation in metric_data:
                metric_value = metric_data[operation]
                
                # Extract reranking information
                reranker = data.get("reranker")
                has_reranking = reranker is not None and reranker != "null"
                
                # Extract document counts
                num_retrieved = data.get("num_retrieved_docs")
                num_final = data.get("num_docs_final")
                
                # Extract other configuration details
                model = data.get("model", "unknown")
                prompt_type = data.get("prompt_type", "unknown")
                hyperparameters = data.get("hyperparameters", {})
                
                config_info = {
                    "file_path": file_path,
                    "metric_value": metric_value,
                    "model": model,
                    "prompt_type": prompt_type,
                    "hyperparameters": hyperparameters,
                    "has_reranking": has_reranking,
                    "reranker": reranker if has_reranking else None,
                    "num_retrieved_docs": num_retrieved,
                    "num_docs_final": num_final,
                    "document_info": _format_document_info(has_reranking, num_retrieved, num_final)
                }
                
                rag_configs.append(config_info)
    
    # Sort by metric value (descending for higher-is-better metrics)
    rag_configs.sort(key=lambda x: x["metric_value"], reverse=True)
    
    # Return top N
    return rag_configs[:top_n]

def _format_document_info(has_reranking: bool, num_retrieved: int, num_final: int) -> str:
    """
    Helper function to format document information.

    Args:
        has_reranking (bool): indicates if re-ranking enabled for experiment or not
        num_retrieved (int): how many documents were retrieved
        num_final (int): how many documents were returned after re-ranking if enabled
    """

    # Default to this if retrieval info not present
    if num_retrieved is None:
        return "No document info"
    
    # If re-ranking enabled
    if has_reranking:
        if num_final is not None:
            reduction = num_retrieved - num_final
            reduction_percent = (reduction / num_retrieved) * 100 if num_retrieved > 0 else 0
            return "{} → {} docs ({}% reduction)".format(num_retrieved, num_final, reduction_percent:.1f)
        else:
            return "{} docs (reranked, final count unknown)".format(num_retrieved)
    # If not, just return number of retrieved docs and indicate that no re-ranking took place
    else:
        return "{} docs (no reranking)".format(num_retrieved)

def plot_top_rag_configs_with_reranking(all_results: List[Dict[str, Any]], 
                                       metric_name: str,
                                       operation: str = "mean",
                                       top_n: int = 10,
                                       save_path: str = "top_rag_configs_with_reranking.png") -> None:
    """
    Create a horizontal bar plot showing top RAG configurations with reranking information.

    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to rank by
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
        top_n: Number of top configurations to return
        save_path (str): where to save generated graph
    """

    top_configs = get_top_rag_configs_with_reranking(all_results, metric_name, operation, top_n)
    
    if not top_configs:
        print(f"No RAG configurations found for {metric_name}")
        return
    
    # Prepare data for plotting
    config_labels = []
    metric_values = []
    colours = []
    reranking_info = []
    
    for i, config in enumerate(top_configs):
        # Create a detailed label with model, prompt type, and document info
        model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
        prompt_type = config["prompt_type"]
        document_info = config["document_info"]
        
        # Format hyperparameters (optional, can be removed if too cluttered)
        hyperparams = config["hyperparameters"]
        hp_str = ""
        if hyperparams:
            hp_parts = []
            for key, value in list(hyperparams.items())[:3]:  # Limit to first 3 hyperparams
                if isinstance(value, (int, float)):
                    hp_parts.append(f"{key}={value}")
                else:
                    hp_parts.append(f"{key}={str(value)[:8]}...")
            hp_str = f" | {", ".join(hp_parts)}"
        
        label = f"{i+1}. {model} ({prompt_type}){hp_str}\n   {document_info}"
        
        config_labels.append(label)
        metric_values.append(config["metric_value"])
        
        # Colour based on reranking
        colours.append(GREEN_DARK if config["has_reranking"] else GREEN_LIGHT)
        
        # Reranking status for legend
        reranking_info.append("With Reranking" if config["has_reranking"] else "No Reranking")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, max(8, top_n * 0.7)))
    
    bars = ax.barh(config_labels, metric_values, color=colours, alpha=0.8)
    
    ax.set_xlabel(f"{metric_name.upper()} Score")
    ax.set_title(f"Top {top_n} RAG Configurations - {metric_name.upper()} ({operation.upper()})")
    ax.grid(axis="x", alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, metric_values):
        width = bar.get_width()
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2,
               f"{value:.4f}", ha="left", va="center", fontweight="bold")
    
    # Create custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=GREEN_DARK, alpha=0.8, label="With Reranking"),
        Patch(facecolor=GREEN_LIGHT, alpha=0.8, label="No Reranking")
    ]
    ax.legend(handles=legend_elements, loc="lower right")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    # Print detailed summary
    print(f"\nTop {top_n} RAG Configurations for {metric_name} ({operation}):")
    print("=" * 80)
    
    reranking_count = sum(1 for config in top_configs if config["has_reranking"])
    no_reranking_count = len(top_configs) - reranking_count
    
    print(f"Summary: {reranking_count} with reranking, {no_reranking_count} without reranking")
    print("-" * 80)
    
    for i, config in enumerate(top_configs):
        model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
        rerank_status = "✓ Reranked" if config["has_reranking"] else "✗ No Rerank"
        print(f"{i+1:2d}. {model:30s} | {config["metric_value"]:.4f} | {rerank_status:12s} | {config["document_info"]}")

def plot_reranking_comparison_summary(all_results: List[Dict[str, Any]], 
                                    metric_name: str,
                                    operation: str = "mean",
                                    top_n: int = 5,
                                    save_path: str = "reranking_comparison_summary.png") -> None:
    """
    Create a summary comparison showing the best configurations side by side.

    Args:
        all_results: List of result dictionaries
        metric_name: Name of the metric to rank by
        operation: Operation to perform ("mean", "min", "max", "median", "std", "count")
        top_n: Number of top configurations to return
        save_path (str): where to save generated graph
    """
    # Get top configurations by reranking status
    all_rag_configs = get_top_rag_configs_with_reranking(all_results, metric_name, operation, 1000)
    
    with_reranking = [config for config in all_rag_configs if config["has_reranking"]]
    without_reranking = [config for config in all_rag_configs if not config["has_reranking"]]
    
    top_with_reranking = with_reranking[:top_n]
    top_without_reranking = without_reranking[:top_n]
    
    if not top_with_reranking and not top_without_reranking:
        print(f"No RAG configurations found for {metric_name}")
        return
    
    # Create figure with proper subplot layout - use 2 rows, 1 column for text boxes
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.3)
    
    # Create subplots
    ax = fig.add_subplot(gs[0])
    ax_bottom = fig.add_subplot(gs[1]) 
    ax_bottom.axis("off")
    
    green_dark = GREEN_DARK
    green_light = GREEN_LIGHT
    
    # Prepare data for side-by-side comparison
    labels = []
    with_rerank_values = []
    without_rerank_values = []
    
    max_configs = max(len(top_with_reranking), len(top_without_reranking))
    
    for i in range(max_configs):
        labels.append(f"Rank {i+1}")
        
        if i < len(top_with_reranking):
            with_rerank_values.append(top_with_reranking[i]["metric_value"])
        else:
            with_rerank_values.append(0)
        
        if i < len(top_without_reranking):
            without_rerank_values.append(top_without_reranking[i]["metric_value"])
        else:
            without_rerank_values.append(0)
    
    x = np.arange(len(labels))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, with_rerank_values, width, label="With Reranking", 
                   color=green_dark, alpha=0.8)
    bars2 = ax.bar(x + width/2, without_rerank_values, width, label="Without Reranking", 
                   color=green_light, alpha=0.8)
    
    ax.set_xlabel("Ranking Position")
    ax.set_ylabel(f"{metric_name.upper()} Score")
    ax.set_title(f"Top {top_n} Configurations: Reranking vs No Reranking\n{metric_name.upper()} ({operation.upper()})", 
                fontweight="bold", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    
    # Add value labels
    for bars, values in [(bars1, with_rerank_values), (bars2, without_rerank_values)]:
        for bar, value in zip(bars, values):
            if value > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f"{value:.4f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
    
    # Create configuration details for WITH reranking (left text box)
    with_rerank_text = "CONFIGURATIONS WITH RERANKING:\n"
    with_rerank_text += "=" * 40 + "\n\n"
    
    if top_with_reranking:
        for i, config in enumerate(top_with_reranking, 1):
            model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
            prompt_type = config["prompt_type"]
            with_rerank_text += f"{i}. {model}\n"
            with_rerank_text += f"   Type: {prompt_type}\n"
            with_rerank_text += f"   Score: {config["metric_value"]:.4f}\n"
            with_rerank_text += f"   Docs: {config["document_info"]}\n\n"
    else:
        with_rerank_text += "No configurations found\n"
    
    # Add performance summary for with reranking
    if top_with_reranking:
        avg_with_rerank = np.mean([c["metric_value"] for c in top_with_reranking])
        with_rerank_text += f"Average Score: {avg_with_rerank:.4f}\n"
        with_rerank_text += f"Best Score: {top_with_reranking[0]["metric_value"]:.4f}\n"
    
    # Create configuration details for WITHOUT reranking (right text box)
    without_rerank_text = "CONFIGURATIONS WITHOUT RERANKING:\n"
    without_rerank_text += "=" * 40 + "\n\n"
    
    if top_without_reranking:
        for i, config in enumerate(top_without_reranking, 1):
            model = config["model"].split("/")[-1] if "/" in config["model"] else config["model"]
            prompt_type = config["prompt_type"]
            without_rerank_text += f"{i}. {model}\n"
            without_rerank_text += f"   Type: {prompt_type}\n"
            without_rerank_text += f"   Score: {config["metric_value"]:.4f}\n"
            without_rerank_text += f"   Docs: {config["document_info"]}\n\n"
    else:
        without_rerank_text += "No configurations found\n"
    
    # Add performance summary for without reranking
    if top_without_reranking:
        avg_without_rerank = np.mean([c["metric_value"] for c in top_without_reranking])
        without_rerank_text += f"Average Score: {avg_without_rerank:.4f}\n"
        without_rerank_text += f"Best Score: {top_without_reranking[0]["metric_value"]:.4f}\n"
    
    # Add text boxes positioned manually in the bottom area
    # Left text box (with reranking)
    ax_bottom.text(0.05, 0.95, with_rerank_text, transform=ax_bottom.transAxes, fontsize=11,
                  verticalalignment="top", fontfamily="monospace", fontweight="bold",
                  bbox=dict(boxstyle="round,pad=0.8", facecolor=green_dark, alpha=0.2, edgecolor=green_dark))
    
    # Right text box (without reranking) - positioned at 0.55 instead of 0.05 to be on the right side
    ax_bottom.text(0.55, 0.95, without_rerank_text, transform=ax_bottom.transAxes, fontsize=11,
                  verticalalignment="top", fontfamily="monospace", fontweight="bold",
                  bbox=dict(boxstyle="round,pad=0.8", facecolor=green_light, alpha=0.2, edgecolor=green_light))
    
    # Add overall comparison if both categories have data
    if top_with_reranking and top_without_reranking:
        best_with_rerank = top_with_reranking[0]["metric_value"]
        best_without_rerank = top_without_reranking[0]["metric_value"]
        avg_with_rerank = np.mean([c["metric_value"] for c in top_with_reranking])
        avg_without_rerank = np.mean([c["metric_value"] for c in top_without_reranking])
        
        comparison_text = f"OVERALL COMPARISON:\n"
        comparison_text += f"Best with reranking:    {best_with_rerank:.4f}\n"
        comparison_text += f"Best without reranking: {best_without_rerank:.4f}\n"
        comparison_text += f"Difference:             {best_with_rerank - best_without_rerank:+.4f}\n"
        comparison_text += f"Average with reranking:    {avg_with_rerank:.4f}\n"
        comparison_text += f"Average without reranking: {avg_without_rerank:.4f}\n"
        comparison_text += f"Average difference:        {avg_with_rerank - avg_without_rerank:+.4f}\n"
        
        # Add comparison text to the graph area
        ax.text(0.02, 0.3, comparison_text, transform=ax.transAxes, fontsize=10,
               verticalalignment="top", fontfamily="monospace", fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Reranking comparison summary saved to {save_path}")

###### END OF UTILITY FUNCTIONS


# First, need to ensure that all json files have flat structure to enable easy plotting
fix_nested_json_evaluation_files("./results")

# Also, need to make sure that "rag" or "llm" type is added to files (it is stored in file name, just easier to access in json)
add_type_property_to_result_files(all_results)

##### START OF PLOT FUNCTION CALLs

# Now, get sanitised results files for plotting
all_results = read_all_json_files_as_list("./results")

# Plot that shows distribution of experiments for "rag" and "llm"
plot_file_distribution_pie(all_results, "graphs/llm_vs_rag_distribution_pie.png")

# F1 plots for all results (both "rag" and "llm" experiments) - max, mean, min
f1_max_results = compare_performance_by_type(all_results, "bert_f1", "max")
f1_mean_results = compare_performance_by_type(all_results, "bert_f1", "mean")
f1_min_results = compare_performance_by_type(all_results, "bert_f1", "min")


# Show best result for F1 for RAG vs LLM (side by side)
simple_comparison_plot(
    f1_max_results["rag"]["computed_value"], 
    f1_max_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - F1 (Best Result)", 
    "Value",
    "./graphs/llm_vs_rag_f1_max.png"
)

# Show worst result for F1 for RAG vs LLM (side by side)
simple_comparison_plot(
    f1_min_results["rag"]["computed_value"], 
    f1_min_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - F1 (Worst Result)", 
    "Value",
    "./graphs/llm_vs_rag_f1_min.png"
)

# Show average results for F1 for RAG vs LLM (side by side)
simple_comparison_plot(
    f1_mean_results["rag"]["computed_value"], 
    f1_mean_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - F1 (Mean Result)", 
    "Mean Value",
    "./graphs/llm_vs_rag_f1_mean.png"
)


# Rouge 1 plots (includes both RAG & LLM)
rouge1_max_results = compare_performance_by_type(all_results, "rouge1_score", "max")
rouge1_mean_results = compare_performance_by_type(all_results, "rouge1_score", "mean")
rouge1_min_results = compare_performance_by_type(all_results, "rouge1_score", "min")

# Show best result for Rouge 1 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge1_max_results["rag"]["computed_value"], 
    rouge1_max_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 1 (Best Result)", 
    "Value",
    "./graphs/llm_vs_rag_rouge1_max.png"
)

# Show worst result for Rouge 1 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge1_min_results["rag"]["computed_value"], 
    rouge1_min_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 1 (Worst Result)", 
    "Value",
    "./graphs/llm_vs_rag_rouge1_min.png"
)

# Show mean result for Rouge 1 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge1_mean_results["rag"]["computed_value"], 
    rouge1_mean_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 1 (Mean Result)", 
    "Mean Value",
    "./graphs/llm_vs_rag_rouge1_mean.png"
)

# Rouge 2 plots (including both LLM & RAG experiments)
rouge2_max_results = compare_performance_by_type(all_results, "rouge2_score", "max")
rouge2_mean_results = compare_performance_by_type(all_results, "rouge2_score", "mean")
rouge2_min_results = compare_performance_by_type(all_results, "rouge2_score", "min")

# Show best result for Rouge 2 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge2_max_results["rag"]["computed_value"], 
    rouge2_max_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 2 (Best Result)", 
    "Value",
    "./graphs/llm_vs_rag_rouge2_max.png"
)

# Show worst result for Rouge 2 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge2_min_results["rag"]["computed_value"], 
    rouge2_min_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 2 (Worst Result)", 
    "Value",
    "./graphs/llm_vs_rag_rouge2_min.png"
)

# Show mean result for Rouge 2 for RAG vs LLM (side by side)
simple_comparison_plot(
    rouge2_mean_results["rag"]["computed_value"], 
    rouge2_mean_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge 2 (Mean Result)", 
    "Mean Value",
    "./graphs/llm_vs_rag_rouge2_mean.png"
)

# Rouge L plots (include RAG & LLM experiments)
rougeL_max_results = compare_performance_by_type(all_results, "rougeL_score", "max")
rougeL_mean_results = compare_performance_by_type(all_results, "rougeL_score", "mean")
rougeL_min_results = compare_performance_by_type(all_results, "rougeL_score", "min")

# Show best result for Rouge L for RAG vs LLM (side by side)
simple_comparison_plot(
    rougeL_max_results["rag"]["computed_value"], 
    rougeL_max_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge L (Best Result)", 
    "Value",
    "./graphs/llm_vs_rag_rougeL_max.png"
)

# Show worst result for Rouge L for RAG vs LLM (side by side)
simple_comparison_plot(
    rougeL_min_results["rag"]["computed_value"], 
    rougeL_min_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge L (Worst Result)", 
    "Value",
    "./graphs/llm_vs_rag_rougeL_min.png"
)

# Show average result for Rouge L for RAG vs LLM (side by side)
simple_comparison_plot(
    rougeL_mean_results["rag"]["computed_value"], 
    rougeL_mean_results["llm"]["computed_value"], 
    "RAG", 
    "LLM", 
    "Rag vs LLM - Rouge L (Mean Result)", 
    "Mean Value",
    "./graphs/llm_vs_rag_rougeL_mean.png"
)

# Zero shot LLM as a judge plots (including all experiment results)
plot_label_comparison(all_results, "graphs/label_comparison.png")
plot_label_pie_charts(all_results, "graphs/label_pie_charts.png")
plot_probability_comparison(all_results, "graphs/probability_comparison.png")

# Plot F1 scores by model and by experiment type (individual graphs for mean scores as well as max scores for each model)
plot_model_comparison_by_type(all_results, "bert_f1", "mean", "graphs/model_comparison_by_f1_mean.png")
plot_model_comparison_by_type(all_results, "bert_f1", "max", "graphs/model_comparison_by_f1_max.png")

# Plot Rouge 1 scores by model and by experiment type (individual graphs for mean scores as well as max scores for each model)
plot_model_comparison_by_type(all_results, "rouge1_score", "max", "graphs/model_comparison_by_rouge1_max.png")
plot_model_comparison_by_type(all_results, "rouge1_score", "mean", "graphs/model_comparison_by_rouge1_mean.png")

# Plot Rouge 2 scores by model and by experiment type (individual graphs for mean scores as well as max scores for each model)
plot_model_comparison_by_type(all_results, "rouge2_score", "max", "graphs/model_comparison_by_rouge2_max.png")
plot_model_comparison_by_type(all_results, "rouge2_score", "mean", "graphs/model_comparison_by_rouge2_mean.png")

# Plot Rouge L scores by model and by experiment type (individual graphs for mean scores as well as max scores for each model)
plot_model_comparison_by_type(all_results, "rougeL_score", "max", "graphs/model_comparison_by_rougeL_max.png")
plot_model_comparison_by_type(all_results, "rougeL_score", "mean", "graphs/model_comparison_by_rougeL_mean.png")

# Hyperparameter graphs - extract top 10 performing scores on average for each method (rag & llm) for each metric
# F1
plot_top_configs_with_hyperparams(all_results, "bert_f1", "mean", 10, save_path="graphs/top_configs_f1_with_hyperparams.png")
# Rouge 1
plot_top_configs_with_hyperparams(all_results, "rouge1_score", "mean", 10, save_path="graphs/top_configs_rouge1_with_hyperparams.png")
# Rouge 2
plot_top_configs_with_hyperparams(all_results, "rouge2_score", "mean", 10, save_path="graphs/top_configs_rouge2_with_hyperparams.png")
# Rouge L
plot_top_configs_with_hyperparams(all_results, "rougeL_score", "mean", 10, save_path="graphs/top_configs_rougeL_with_hyperparams.png")

# LLM as a judge - extract top 10 performing hyperparameter configurations (ones that had highest number of answers labelled as entailing the ground truth)
plot_top_entailment_configs(all_results, 10, save_path="graphs/top_entailment_configs.png")

# Prompt Engineering - Plot distribution of prompts used across experiments
plot_prompt_distribution_pie(all_results, "graphs/prompt_distribution_pie.png")

# Plot top 10 hyperparameter configurations by LLM as a judge task (to enable comparison between top for RAG and top for LLM)
plot_top_entailment_configs(all_results, 10, "rag", "graphs/top_rag_entailment_configs.png")
plot_top_entailment_configs(all_results, 10, "llm", "graphs/top_llm_entailment_configs.png")

# Prompt Engineering - Performance of each prompt
# F1 - first one shows F1 average score across all experiments
plot_prompt_comparison_simple(all_results, "bert_f1", "mean", save_path="graphs/prompt_comparison_all_f1.png")
# Second one shows F1 average score across all RAG experiments
plot_prompt_comparison_simple(all_results, "bert_f1", "mean", "rag", save_path="graphs/prompt_comparison_rag_f1.png")
# Third one shows F1 average score across all LLM experiments
plot_prompt_comparison_simple(all_results, "bert_f1", "mean", "llm", save_path="graphs/prompt_comparison_llm_f1.png")

# Rouge 1 - first one shows Rouge 1 average score across all experiments
plot_prompt_comparison_simple(all_results, "rouge1_score", "mean", save_path="graphs/prompt_comparison_all_rouge1.png")
# Second one shows Rouge 1 average score across all RAG experiments
plot_prompt_comparison_simple(all_results, "rouge1_score", "mean", "rag", save_path="graphs/prompt_comparison_rag_rouge1.png")
# Third one shows Rouge 1 average score across all LLM experiments
plot_prompt_comparison_simple(all_results, "rouge1_score", "mean", "llm", save_path="graphs/prompt_comparison_llm_rouge1.png")

# Rouge 2 - first one shows Rouge 1 average score across all experiments
plot_prompt_comparison_simple(all_results, "rouge2_score", "mean", save_path="graphs/prompt_comparison_all_rouge2.png")
# Second one shows Rouge 2 average score across all RAG experiments
plot_prompt_comparison_simple(all_results, "rouge2_score", "mean", "rag", save_path="graphs/prompt_comparison_rag_rouge2.png")
# Third one shows Rouge 2 average score across all LLM experiments
plot_prompt_comparison_simple(all_results, "rouge2_score", "mean", "llm", save_path="graphs/prompt_comparison_llm_rouge2.png")

# Rouge L - first one shows Rouge L average score across all experiments
plot_prompt_comparison_simple(all_results, "rougeL_score", "mean", save_path="graphs/prompt_comparison_all_rougeL.png")
# Second one shows Rouge L average score across all RAG experiments
plot_prompt_comparison_simple(all_results, "rougeL_score", "mean", "rag", save_path="graphs/prompt_comparison_rag_rougeL.png")
# Third one shows Rouge L average score across all LLM experiments
plot_prompt_comparison_simple(all_results, "rougeL_score", "mean", "llm", save_path="graphs/prompt_comparison_llm_rougeL.png")

# These graphs focus on re-ranking for RAG experiments (impact of with & without)

# Plot top 10 hyperparameter configurations for F1 average scores for RAG experiments (also show re-ranking stats)
plot_top_rag_configs_with_reranking(all_results, "bert_f1", "mean", 10, "graphs/top_rag_f1_re_rank_impact.png")

# Plot top 5 scores for RAG experiments for F1 with re-ranking enabled vs those without the technique
# To enable easy visualisation of impact
plot_reranking_comparison_summary(all_results, "bert_f1", "mean", 5, "graphs/reranking_comparison_summary_f1_mean.png")

# Plot top 10 hyperparameter configurations for Rouge 1 average scores for RAG experiments (also show re-ranking stats)
plot_top_rag_configs_with_reranking(all_results, "rouge1_score", "mean", 10, "graphs/top_rag_rouge1_re_rank_impact.png")

# Plot top 5 scores for RAG experiments for Rouge 1 with re-ranking enabled vs those without the technique
# To enable easy visualisation of impact
plot_reranking_comparison_summary(all_results, "rouge1_score", "mean", 5, "graphs/reranking_comparison_summary_rouge1_mean.png")

# Plot top 10 hyperparameter configurations for Rouge 2 average scores for RAG experiments (also show re-ranking stats)
plot_top_rag_configs_with_reranking(all_results, "rouge2_score", "mean", 10, "graphs/top_rag_rouge2_re_rank_impact.png")

# Plot top 5 scores for RAG experiments for Rouge 2 with re-ranking enabled vs those without the technique
# To enable easy visualisation of impact
plot_reranking_comparison_summary(all_results, "rouge2_score", "mean", 5, "graphs/reranking_comparison_summary_rouge2_mean.png")

# Plot top 10 hyperparameter configurations for Rouge L average scores for RAG experiments (also show re-ranking stats)
plot_top_rag_configs_with_reranking(all_results, "rougeL_score", "mean", 10, "graphs/top_rag_rougeL_re_rank_impact.png")

# Plot top 5 scores for RAG experiments for Rouge L with re-ranking enabled vs those without the technique
# To enable easy visualisation of impact
plot_reranking_comparison_summary(all_results, "rougeL_score", "mean", 5, "graphs/reranking_comparison_summary_rougeL_mean.png")


