# Citizen Information Chat - Thesis MSc in Artifical Intelligence @ University of Limerick

The Citizen Information Chat project explored whether a pre-trained large language model's (LLM) performance could be improved with the implementation of retrieval-augmented generation (RAG). The target task was to accurately reply to a user's queries on a range of topics for which publicly available information is published on the Citizen Information site.

Focus on open-source models with each sourced on the Hugging Face platform.

Additionally, exploration took place to determine if model scaling holds true for this target task as well with experiments conducted across three models:

- Mistral Instruct 7B
- Llama Instruct 3B
- Qwen Instruct 1.5B

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
- DeepEval: open-source LLM evaluation framework, used to evaluate the retrieval piece of RAG by using third-party LLM (in this case DeepSeek 14B Distilled) to determine scores on contextual relevancy, contextual precision, contextual recall, faithfulness, answer relevancy

#### Repository Structure

Key directories shown below

- data
- notebooks
- scripts

#### Getting started

- `python3 -m venv . `
- `source ./bin/activate`
- `pip3 install -r ../requirements.txt`

#### Running Tests

```
python -m unittest discover -s tests
```

##### Scraping

Sitemap is at https://www.citizensinformation.ie/sitemap.xml

#### Commands

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
