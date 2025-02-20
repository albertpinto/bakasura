from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
import os
from tools.txt_PDF_tool import PDFConversionTool
from crewai_tools import FileWriterTool

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not found. Gemini models will not be available.")
    genai = None


import sys
import warnings
from datetime import datetime
from pydantic import BaseModel, validator, ValidationError
import re

def count_sentences(text: str) -> int:
    # Naively count sentences splitting on period, exclamation or question mark.
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

class CollegeEssayModel(BaseModel):
    heading: str
    opening_paragraph: str
    body_paragraphs: list[str]
    closing_paragraph: str

    @validator('heading')
    def check_heading(cls, v):
        words = v.split()
        if len(words) < 4:
            raise ValueError("Heading must be at least 4 words")
        return v

    @validator('opening_paragraph')
    def check_opening_paragraph(cls, v):
        sentence_count = count_sentences(v)
        if sentence_count < 2 or sentence_count > 3:
            raise ValueError("Opening paragraph must have 2-3 sentences")
        return v

    @validator('body_paragraphs')
    def check_body_paragraphs(cls, v):
        if not (2 <= len(v) <= 3):
            raise ValueError("There must be 2-3 body paragraphs")
        for paragraph in v:
            if count_sentences(paragraph) < 3:
                raise ValueError("Each body paragraph must have at least 3 sentences")
        return v

    @validator('closing_paragraph')
    def check_closing_paragraph(cls, v):
        sentence_count = count_sentences(v)
        if sentence_count < 2 or sentence_count > 3:
            raise ValueError("Closing paragraph must have 2-3 sentences")
        return v

@CrewBase
class CollegeEssay():
	"""This is the optimal crew for generating a college essay version 2 and can use
	any openAI and other models to generate the essay"""

	def __init__(self, model, output_file):
		self.model = model
		self.output_file = output_file
		self.llm = self._set_llm()

	def _set_llm(self):
		if self.model.startswith('gemini'):
			if genai is None:
				raise ImportError("google-generativeai package is required for Gemini models")
			# Configure Gemini API
			api_key = os.getenv('GOOGLE_API_KEY')
			if not api_key:
				raise ValueError("GOOGLE_API_KEY environment variable is not set")
			genai.configure(api_key=api_key)
			# Always specify the model name for Gemini
			if self.model == 'gemini/gemini-1.5-flash':
				return LLM(provider="gemini", 
			   			  model="gemini/gemini-1.5-flash",
						  api_key=os.getenv('GOOGLE_API_KEY'))
			else:
				return LLM(provider="gemini", model=self.model)
		elif self.model in ['gpt-4o', 'gpt-3.5-turbo', 'claude-2', 'o1-preview', 'o1-mini']:
			return self.model
		else:
			return LLM(model="ollama/"+ self.model, base_url="http://localhost:11434")
	@agent
	def essay_generator(self) -> Agent:
		# The json_output parameter automatically enforces the CollegeEssayModel.
		# Ensure your LLM returns valid JSON matching:
		# {
		#   "opening_paragraph": <str>,
		#   "body_paragraphs": [<str>, ...],
		#   "closing_paragraph": <str>
		# }
		return Agent(
			config=self.agents_config['essay_generator'],
			llm=self.llm,
			verbose=True
		)
		
	# Optionally, you can further enforce validation like so:
	# result = self.essay_generator().execute_task(...) 
	# validated_output = CollegeEssayModel.parse_obj(result)

	@agent
	def critic_reviewer(self) -> Agent:
		return Agent(
			config=self.agents_config['critic_reviewer'],
			llm=self.llm,
			allow_delegation=True,
			verbose=True,
			tools=[FileReadTool(), FileWriterTool()],  # Make sure it reads the essay and updates it
    )
	@agent
	def markdown(self) -> Agent:
		return Agent(
			config=self.agents_config['markdown'],
			verbose=True,
		)
	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def essay_task(self) -> Task:
		return Task(
			config=self.tasks_config['essay_task'],
			allow_delegation=True,
			output_file= self.output_file+ ".md",
			verbose=True,

		)


	@task
	def critic_task(self) -> Task:
		return Task(
			config=self.tasks_config['critic_task'],
			output_file= self.output_file+ ".md", # Ensure critic writes back to the essay file
			allow_delegation=True,
			verbose=True,
		)
	@task
	def markdown_task(self) -> Task:
		return Task(
			config=self.tasks_config['markdown_task'],
			output_file= self.output_file+ ".md",
			verbose=True
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the CollegeEssay crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=[self.essay_generator(), self.critic_reviewer()], 
			tasks=[self.essay_task(), self.critic_task()],
			process=Process.sequential,  # Ensure the essay is written before critique
			verbose=True
			
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
	def convert_to_pdf(self,input_file, output_file):
		pdf_tool = PDFConversionTool(input_file_path=input_file, output_file_path=output_file)
		return pdf_tool._run()