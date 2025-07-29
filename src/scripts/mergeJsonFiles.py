import json
import os
import random
from datetime import datetime


"""
Script to merge the synthetic datasets for fine-tuning 
(one from DeepSeek QA generation from Citizen information chunks, other from Oireachtas API data)
"""

def load_standard_qa_data(file_path: str):
    """
    Load and process the data from the DeepSeek QA generation from Citizen information chunks

    Args:
        file_path: where is the file to be read
    """

    print("Loading standard QA data from {}...".format(file_path))
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    processed_data = []
    # Loop over the data (it is list of dicts)
    for item in data:
        # Check if item has required fields for fine-tuning
        if all(key in item for key in ["chunk_text", "question", "answer"]):
            # Clean the text by calling strip on each field
            chunk_text = item["chunk_text"].strip()
            question = item["question"].strip()
            answer = item["answer"].strip()
            
            # Only include if all values present
            if chunk_text and question and answer:
                # Note standard format here (same done below for Oireachtas API so that they can be merged together)
                processed_data.append({
                    "chunk_text": chunk_text,
                    "question": question,
                    "answer": answer,
                    "prompt": item.get("prompt", "").strip(),
                    "metadata": item.get("metadata", {}),
                    "source": "standard_qa"
                })
    
    # Debug to see how many QA pairs were updated then return
    print(f"Processed {len(processed_data)} items from standard QA dataset")
    return processed_data

def load_oireachtas_data(file_path):
    """
    Load and process the Oireachtas Dáil Éireann Q&A dataset.

    Args:
        file_path (str): where the oireachtas data json file is located
    """

    print("Loading Oireachtas data from {}...".format(file_path))
    
    # Try read the file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    processed_data = []
    
    for item in data:
        try:
            # Use the formatted fields that are already processed
            formatted_question = item.get("formatted_question", "").strip()
            formatted_answer = item.get("formatted_answer", "").strip()
            
            # Create context from the original question and metadata
            context_parts = []
            
            # Add the original question
            if "extracted_question" in item:
                context_parts.append("Original Question: {}".format(item["extracted_question"]))
            
            # Extract debate section
            if "debateSection" in item and "showAs" in item["debateSection"]:
                debate_section = item["debateSection"]["showAs"]
                if debate_section:
                    context_parts.append("Debate Section: {}".format(debate_section))
            
            # Add date if available
            if "date" in item:
                context_parts.append("Date: {}".format(item["date"]))
            
            # Add member info if available
            if "by" in item and "showAs" in item["by"]:
                member = item["by"]["showAs"]
                if member:
                    context_parts.append("Asked by: {}".format(member))
            
            # Add house info if available
            if "house" in item and "showAs" in item["house"]:
                house = item["house"]["showAs"]
                if house:
                    context_parts.append(f"House: {house}")
            
            # Use this method to ensure spacing between the actual parts of the context
            context = "\n\n".join(context_parts)
            
            # Skip if we don't have both question and answer
            if formatted_question and formatted_answer and context:
                processed_data.append({
                    "chunk_text": context,
                    "question": formatted_question,
                    "answer": formatted_answer,
                    "prompt": f"Based on the parliamentary question and debate context, provide a clear and concise answer.",
                    "metadata": {
                        "source": "oireachtas",
                        "date": item.get("date", ""),
                        "house": item.get("house", {}).get("showAs", ""),
                        "question_type": item.get("questionType", ""),
                        "debate_section": item.get("debateSection", {}).get("showAs", ""),
                        "member": item.get("by", {}).get("showAs", ""),
                        "question_number": item.get("questionNumber", "")
                    },
                    "source": "oireachtas"
                })
        
        except Exception as e:
            print(f"Error processing Oireachtas item: {e}")
            continue
    
    # Debug statement to inform how many QA items were processed in the file, then return
    print("Processed {} items from Oireachtas dataset".format(len(processed_data)))
    return processed_data

def merge_datasets(standard_data, oireachtas_data, output_file="merged_final_qa_dataset.json"):
    """
    Merge the two individual datasets and create the final training dataset that will be used for fine-tuning

    Args:
        standard_data: DeepSeek QA list which are based on individual Citizen Information site document chunks
        oireachtas_data: DeepSeek QA list which are based on reformulation of leaders political questions in Dáil Éireann
        output_file: where to save the merge data
    """
    
    # Combine datasets
    merged_data = standard_data + oireachtas_data
    
    # Shuffle the data (to ensure for training, it is jumbled)
    random.shuffle(merged_data)
    
    print("Total merged items: {}".format(len(merged_data)))
    
    # Save merged dataset to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print("Merged dataset saved to: {}".format(output_file))
    
    return merged_data

def main():
    # Set random seed for reproducible results (when using the random module)
    random.seed(42)
    
    print("QA Dataset Merger for Mistral 7B Fine-tuning")
    print("*" * 60)
    
    # Expected File paths
    standard_qa_file = "documents/merged_qa_docs_dataset.json"
    oireachtas_file = "documents/merged_qa_oireachtas_dataset.json"
    
    # Check if files exist
    if not os.path.exists(standard_qa_file):
        print(f"Error: {standard_qa_file} not found!")
        return
    
    if not os.path.exists(oireachtas_file):
        print(f"Error: {oireachtas_file} not found!")
        return
    
    # Load datasets
    standard_data = load_standard_qa_data(standard_qa_file)
    oireachtas_data = load_oireachtas_data(oireachtas_file)
    
    # Merge datasets
    merged_data = merge_datasets(standard_data, oireachtas_data)
    
    print("\nDataset merge completed!")
    print("Total examples: {}".format(len(merged_data)))
    print("Standard QA examples: {}".format(len(standard_data)))
    print("Oireachtas examples: {}".format(len(oireachtas_data)))
    print(f"\nFiles created:")
    print(f"  - merged_final_qa_dataset.json (merged raw data)")

if __name__ == "__main__":
    main() 