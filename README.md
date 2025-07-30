# Citizen Information Chat - Thesis for MSc in Artificial Intelligence @ University of Limerick

## Overview

The Citizen Information Chat project explored whether a pre-trained large language model's (LLM) performance could be improved with the implementation of retrieval-augmented generation (RAG). The target task was to accurately reply to a user's queries on a range of topics for which publicly available information is published on the Citizen Information site.

Focus on open-source models with each sourced on the [Hugging Face](https://huggingface.co/) platform.

Additionally, exploration took place to determine if model scaling holds true for this target task as well with experiments conducted across three models:

- [Mistral Instruct 7B](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3)
- [Llama Instruct 3B](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- [Qwen Instruct 1.5B](https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct)

Prompt engineering was conducted across a range of different prompt types:

- Zero Shot
- Few Shot
- Instruction
- Persona
- Tree-of-thought
- Chain-of-thought

All experiments were conducted on Google Colaboratory's A100 GPU instance. A 'golden' dataset of 27 QA pairs was manually curated as the ground truth against which all experiments were validated.

Re-ranking, the use of another model to re-rank retrieved documents in RAG, was also explored.

Basic evaluation implemented with the following metrics utilised for comparison

- ROUGE
- F1

Additional evaluation via 'LLM as a judge' via two mechanisms:

- zero-shot labelling (provided ground truth and generated output to an LLM model with task of labelling as 'entailment', 'neutral', 'contradiction'). Target label is 'entailment', that is to say, the generated output 'entails' or supports the ground truth
- DeepEval: open-source LLM evaluation framework, used to evaluate the retrieval piece of RAG by using third-party LLM (in this case DeepSeek 14B Distilled) to determine scores on contextual relevancy, contextual precision, contextual recall, faithfulness, answer relevancy. Note: [Ollama](https://ollama.com/) was used to complete this with a quantised version of Microsoft's [Phi 3](https://huggingface.co/QuantFactory/Phi-3-mini-128k-instruct-GGUF?local-app=ollama) model

## Repository Structure

Key directories shown below

- [data](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data)
- [notebooks](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/notebooks)
- [scripts](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/scripts)

### Data

- [chunks](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/chunks): Scraped Citizen Information documents in chunks in markdown format
- [deepEval](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/deepEval): Raw JSON files that contain DeepEval experiment results
- [fine_tune_dataset](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/fine_tune_dataset): merged_final_qa_dataset.json contains full dataset used for fine-tuning Mistral 7B Instruct Model
- [golden_dataset](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/golden_dataset): The 'golden' QA dataset that I manually curated from the Citizen Information site. All experiments ran against these questions
- [graphs](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/graphs): Graph png files that were generated to support key points in thesis
- [html](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/html): Raw HTML files that were scraped from Citizen Information site
- [markdown](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/markdown): Markdown files which contain sanitised information from HTML files
- [metadata](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/metadata): JSON file that is linked to web-scraping run (contains page that link was found within, timestamp of scrape etc.)
- [results](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/results): Full results from all experiments stored in JSON files.
- [vector_stores](https://github.com/JohnDennehy101/citizenInformationChat/tree/main/src/data/vector_stores): The files that FAISS generated for embedding stores for RAG (note different chunk size used for each)

### Notebooks

All notebooks were run on Google Colaboratory A100 instances (due to GPU compute requirements)

- [Fine-tune Mistral notebook](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/notebooks/Fine_tune_Mistral.ipynb): Notebook that implemented a bare-bones fine-tune of Mistral 7B instruct, published to Hugging Face
- [Generate part of Synthetic Dataset for fine-tuning notebook by using document chunks as context](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/notebooks/Generate_Synthetic_Dataset.ipynb): DeepSeek 14B Distilled model used to generate QA pairs from random Citizen Information document chunks
- [Generate part of Synthetic Dataset for fine-tuning notebook by using Oireachtas API data as context](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/notebooks/Oireachtas_API_synthetic_dataset.ipynb): Dáil Éireann leader questions used as context for DeepSeek 14B Distilled to summarise and extract clear QA pair from statement
- [RAG vs LLM](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/notebooks/RAG_vs_LLM.ipynb): Notebook which was used to run all experiments comparing RAG vs LLM, prompt types etc.

### Scripts

All scripts were run on my local machine (Macbook Pro M2 Max) for ease of development (and no requirement for GPU)

- [deepEval/deepEval.py](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/scripts/deepEval/deepEval.py): Ran DeepEval locally on top-performing RAG configurations (LLM as a judge)
- [deepEval/visualisations.py](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/scripts/deepEval/visualisations.py): Script to generate visualisations of deepEval results
- [evaluationGraphs.py](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/scripts/evaluationGraphs.py): Script to generate graphs from evaluation metrics
- [mergeJsonFiles.py](https://github.com/JohnDennehy101/citizenInformationChat/blob/main/src/scripts/mergeJsonFiles.py): Script used to merge fine-tuning dataset sources into one file before fine-tuning could begin

## Development

### Getting started

- `python3 -m venv . `
- `source ./bin/activate`
- `pip3 install -r ../requirements.txt`

### Running Tests

```
python -m unittest discover -s tests
```

### Commands

##### Processing flag converts stored html files to markdown

`python3  main.py --process`

##### Delete markdown files flag clears stored markdown files

`python3  main.py --delete-markdown-files`

##### Chunk flag creates chunks from markdown files and writes chunk files

`python3  main.py --chunk`

##### Delete chunk files flag clears stored chunked markdown files

`python3  main.py --delete-chunk-files`

#### Scrape flag checks existing html files, extracts links within and scrapes for those that are not present in the directory

`python3  main.py --scrape`
