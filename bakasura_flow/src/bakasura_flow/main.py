#!/usr/bin/env python
from random import randint
from logging import getLogger
import sys
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import asyncio
import aiofiles
import io
from fastapi.middleware.cors import CORSMiddleware

from crewai.flow import Flow, listen, start
from bakasura_flow.crews.poem_crew.poem_crew import PoemCrew
from bakasura_flow.config import settings
from bakasura_flow.tools.txt_PDF_tool import PDFConversionTool

app = FastAPI(
    title="Bakasura Flow API",
    description="API for generating poems using CrewAI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's default port
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class PoemRequest(BaseModel):
    language: str = "en"
    theme: str | None = None
    format: str = "txt"  # Add format option: 'txt' or 'pdf'

class PoemResponse(BaseModel):
    poem: str
    created_at: datetime
    sentence_count: int
    theme: str | None
    language: str

class PoemState(BaseModel):
    sentence_count: int = 1
    poem: str = ""
    created_at: datetime = datetime.now()
    theme: str | None = None
    language: str = "en"
    filepath: Path | None = None  # Add this line
    
    class Config:
        arbitrary_types_allowed = True

class PoemFlow(Flow[PoemState]):
    def __init__(self, language="en", theme=None):
        super().__init__()
        self.state.language = language
        self.state.theme = theme

    @start()
    async def generate_sentence_count(self):
        self.state.sentence_count = randint(25,50)

    @listen(generate_sentence_count)
    async def generate_poem(self):
        crew = PoemCrew(
            language=self.state.language,
            theme=self.state.theme
        )
        result = await asyncio.to_thread(
            crew.crew().kickoff,
            inputs={
                "sentence_count": self.state.sentence_count,
                "language": self.state.language,
                "theme": self.state.theme
            }
        )
        self.state.poem = result.raw

    @listen(generate_poem)
    async def save_poem(self):
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = self.state.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"poem_{timestamp}.txt"
        self.state.filepath = output_dir / filename  # Update this line
        
        async with aiofiles.open(self.state.filepath, "w", encoding="utf-8") as f:
            await f.write(self.state.poem)

@app.post("/generate-poem")
async def generate_poem(request: PoemRequest):
    try:
        poem_flow = PoemFlow(language=request.language, theme=request.theme)
        await poem_flow.kickoff_async()
        
        if request.format == "pdf":
            # Convert to PDF and stream it
            output_pdf = io.BytesIO()
            converter = PDFConversionTool(
                input_file_path=str(poem_flow.state.filepath),
                output_file_path=str(poem_flow.state.filepath.with_suffix('.pdf'))
            )
            converter._run()
            
            # Read the PDF file into memory
            with open(poem_flow.state.filepath.with_suffix('.pdf'), 'rb') as pdf_file:
                output_pdf.write(pdf_file.read())
            output_pdf.seek(0)
            
            return StreamingResponse(
                output_pdf,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=poem_{poem_flow.state.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
                }
            )
        
        # Return JSON response for txt format
        return PoemResponse(
            poem=poem_flow.state.poem,
            created_at=poem_flow.state.created_at,
            sentence_count=poem_flow.state.sentence_count,
            theme=poem_flow.state.theme,
            language=poem_flow.state.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
