# CollegeEssay Crew

Welcome to the CollegeEssay Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv

```

## Create your project structure
cd ~/Documents
uv init crewaiprojects --python 3.12
uv sync --upgrade
source .venv/bin/activate


## Install crewAI dependencies

uv add crewai crewai[tools]

## Add crewAI project

uv crewai create crew college-essay or crewai create crew college-essay


### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/college_essay/config/agents.yaml` to define your agents
- Modify `src/college_essay/config/tasks.yaml` to define your tasks
- Modify `src/college_essay/crew.py` to add your own logic, tools and specific args
- Modify `src/college_essay/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ uv run /home/albert/Documents/crewaiprojects/.venv/bin/python /home/albert/Documents/crewaiprojects/college_essay/src/college_essay/college_essay_streaming.py
```

This command initializes the college-essay Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The college-essay Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.


