# Automated Property Submarket Analysis

## Overview
This project implements an AI workflow for **Property Submarket Analysis**, using LangGraph.
![Overview](img/overview.png)

## Setup

### Requirements
- Python 3.11
- RentCast API Key
- ArcGIS Username/Password
- OpenAI API Key

### Environments
Copy the `.env.sample` file to `.env` and fill in your API keys.
```
cp .env.sample .env
```

### Installation
```
pip install -r requirements.txt
```

## Usage

### Launch Demo
```
streamlit run app.py
```

### Run Test
```
python test.py
```

## Workflow
![Workflow](img/workflow.png)

## Files
- `data/`: Test cases
- `output/`: Report files
- `state.py`: State definitions
- `nodes.py`: Node definitions
- `tools.py`: Tool definitions
- `prompts.py`: Prompt templates
- `workflow.py`: Workflow definition
- `config.py`: Config loader 
- `app.py`: Streamlit demo
- `test.py`: Test script