#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from college_essay.crew import CollegeEssay

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    crew = CollegeEssay()
    file_content = crew.get_file_content()
    inputs = {
        'file_content': file_content,
        'program': 'Business',
        'output_essay': 'essay',
        'student': 'Rika Pinto',
    }
    for input in inputs:
        print((input, inputs[input]))
    CollegeEssay().crew().kickoff(inputs=inputs)
    # Convert the generated essay to PDF
    input_file = "/home/albert/Documents/college_essay_version2/essay.md"  # This should match the output_file in essay_task
    output_file = "/home/albert/Documents/college_essay_version2/essay.pdf"
    crew.convert_to_pdf(input_file, output_file)
    try:
        CollegeEssay().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")



