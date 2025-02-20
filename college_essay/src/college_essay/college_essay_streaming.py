import os
import base64
import shutil
import asyncio
import time
import markdown
from weasyprint import HTML # Add this import
from fastapi import FastAPI, Query, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from crew import CollegeEssay
from tools.file_converter import FileConverter

# Initialize FastAPI App and Configure CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Set up upload directory for resume files
UPLOAD_DIR = "college_essay/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)




class StreamingCollegeEssayCrewRunner(CollegeEssay):
    def __init__(self, model,input_file):
        super().__init__(model, input_file)

    def get_file_content(self, file_path):
        """Read content from a file using FileConverter."""
        try:
            return FileConverter.convert_to_text(file_path)
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    def convert_to_pdf(self, input_file, output_file):
        """Convert markdown to PDF using WeasyPrint."""
        try:
            # Read markdown content
            with open(input_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML with extensions
            html_content = markdown.markdown(markdown_content, extensions=['extra'])
            
            # Enhanced HTML template with better styling
            full_html = f"""
                <!DOCTYPE html>
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            @page {{
                                margin: 1in;
                                size: letter;
                            }}
                            body {{
                                font-family: 'Arial', sans-serif;
                                line-height: 1.6;
                                font-size: 12pt;
                                margin: 0;
                                padding: 0;
                            }}
                            h1 {{
                                color: #2c3e50;
                                font-size: 18pt;
                                margin-bottom: 1em;
                            }}
                            h2 {{
                                color: #34495e;
                                font-size: 16pt;
                                margin-top: 1.5em;
                            }}
                            p {{
                                margin-bottom: 1em;
                                text-align: justify;
                            }}
                            .content {{
                                max-width: 8.5in;
                                margin: 0 auto;
                                padding: 1em;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="content">
                            {html_content}
                        </div>
                    </body>
                </html>
            """
            
            # Convert HTML to PDF
            pdf_document = HTML(string=full_html)
            pdf_document.write_pdf(output_file)
            
            if not os.path.exists(output_file):
                raise Exception("PDF file was not created")
                
            return "PDF conversion successful"
        except Exception as e:
            return f"Conversion failed: {str(e)}"

async def college_essay_stream(program: str, student: str, college: str, resume_file_path: str, model: str):
    """
    Generator function to stream the college essay creation process.
    Yields status updates and the final PDF content.
    """
    output_file = student.replace(" ", "-") + "-essay"
    crew_runner = StreamingCollegeEssayCrewRunner(model,output_file)
    
   
    # Load file content
    file_content = crew_runner.get_file_content(resume_file_path)
    yield f"data: File content loaded. Length: {len(file_content)} characters\n\n"
    
    # Prepare inputs
    inputs = {
        'file_content': file_content,
        'program': program,
        'output_essay': "essay",
        'college': college,
        'student': student,
        'model': model
    }
    
    # Stream input information
    for input_key, input_value in inputs.items():
        yield f"data: Input: {input_key} - {input_value[:50]}...\n\n"
        await asyncio.sleep(0.1)
    
    # Execute crew tasks with error handling
    yield "data: Starting crew execution...\n\n"
    custom_crew = crew_runner.crew()

    for agent in custom_crew.agents:
        yield f"data: Agent role:{agent.role} is starting work\n\n"
        yield f"data: Agent goal: {agent.goal} is starting work\n\n"
        yield f"data: Agent backstory:{agent.backstory} is starting work\n\n"
        await asyncio.sleep(0.5)
  
    result = custom_crew.kickoff(inputs=inputs)
    yield f"data: Crew execution completed. Result: {result}\n\n"
         # Convert essay to PDF
    input_file = "/home/albert/Documents/crewaiprojects/" + output_file + ".md"
    output_file = f"/home/albert/Documents/crewaiprojects/"+ output_file +".pdf"
    yield f"data: Converting essay to PDF: {input_file} -> {output_file}\n\n"
    pdf_result = crew_runner.convert_to_pdf(input_file, output_file)
    yield f"data: PDF Conversion Result: {pdf_result}\n\n"

    # Stream PDF content
    with open(output_file, "rb") as pdf_file:
        pdf_content = pdf_file.read()
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        yield f"data: PDF_CONTENT:{pdf_base64}\n\n"
    yield "data: Streaming completed\n\n"

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Endpoint to handle resume file uploads.
    Saves the file to the upload directory and returns the file path.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return JSONResponse(content={"file_path": file_path})

@app.get("/stream_college_essay")
async def stream_college_essay(
    program: str = Query(..., description="Program name"),
    student: str = Query(..., description="Student name"),
    college: str = Query(..., description="College name"),
    resumeFilePath: str = Query(..., description="Path to uploaded resume file"),
    model: str = Query(..., description="Selected language model")):
    """
    Endpoint to stream the college essay generation process.
    Returns a StreamingResponse with real-time updates.
    """
    return StreamingResponse(
        college_essay_stream(program, student, college, resumeFilePath, model),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)