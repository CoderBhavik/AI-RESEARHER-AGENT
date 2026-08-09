# AI RESEARCH AGENT
- This agent uses tavily and beautifulsoup to research on real time news or article.
- It uses sarvam105b model as llm to create report and critic report on the research.
- Also used Streamlit for interactive ui.

## Technologies Used:-
- python 3.13 >=
- streamlit for ui
- langchain more model integration and report generation
- sarvam105b model
- tavily for web based research
- beautifulsoup for scraping data

## Installation :-
1. Create Virtual enviorment:-
    - using python -m venv venv
    - using uv venv

2. Clone git repo:
- git clone https://github.com/CoderBhavik/AI-RESEARHER-AGENT.git


## Project structure :-
AI-RESEARCH-AGENT
├── __init__.py
├── main.py
├── __pycache__
│   ├── agents.cpython-313.pyc
│   ├── main.cpython-313.pyc
│   ├── pipeline.cpython-313.pyc
│   ├── tools.cpython-313.pyc
│   └── ui_helpers.cpython-313.pyc
├── pyproject.toml
├── README.md
├── requirements.txt
├── research
│   ├── agents
│   │   ├── agents.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── agents.cpython-313.pyc
│   │       └── __init__.cpython-313.pyc
│   ├── __init__.py
│   ├── pipeline
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   └── __pycache__
│   │       ├── __init__.cpython-313.pyc
│   │       └── pipeline.cpython-313.pyc
│   ├── __pycache__
│   │   └── __init__.cpython-313.pyc
│   └── tools
│       ├── __init__.py
│       ├── __pycache__
│       │   ├── __init__.cpython-313.pyc
│       │   └── tools.cpython-313.pyc
│       └── tools.py
├── ui
│   ├── app.py
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-313.pyc
│   │   └── ui_helpers.cpython-313.pyc
│   └── ui_helpers.py
└── uv.lock

# Author

CoderBhavik