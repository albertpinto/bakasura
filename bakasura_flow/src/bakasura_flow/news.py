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
from bakasura_flow.crews.news_crew.news_crew import NewsCrew
from bakasura_flow.config import settings
from bakasura_flow.tools.txt_PDF_tool import PDFConversionTool

app = FastAPI(
    title="Bakasura Flow API",
    description="API for generating News using CrewAI",
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

class NewsRequest(BaseModel):
    language: str = "en"
    topic: str | None = None  # Change theme to topic for consistency
    format: str = "txt"

class NewsResponse(BaseModel):
    news: str  # Fix the field name to match the state
    created_at: datetime
    sentence_count: int
    topic: str | None  # Change theme to topic
    language: str

class NewsState(BaseModel):
    sentence_count: int = 1
    news: str = ""
    created_at: datetime = datetime.now()
    topic: str | None = None  # Change theme to topic
    language: str = "en"
    filepath: Path | None = None
    
    class Config:
        arbitrary_types_allowed = True

class NewsFlow(Flow[NewsState]):
    def __init__(self, language="en", topic=None):  # Change theme to topic
        super().__init__()
        self.state.language = language
        self.state.topic = topic  # Change theme to topic

    @start()
    async def generate_sentence_count(self):
        self.state.sentence_count = randint(25,50)

    @listen(generate_sentence_count)
    async def generate_news(self):
        crew = NewsCrew(
            language=self.state.language,
            theme=self.state.topic  # Use topic as theme for crew
        )
        result = await asyncio.to_thread(
            crew.crew().kickoff,
            inputs={
                "sentence_count": self.state.sentence_count,
                "language": self.state.language,
                "topic": self.state.topic,  # Add this line
                "theme": self.state.topic  # Keep this for backward compatibility
            }
        )
        self.state.news = result.raw

    @listen(generate_news)
    async def save_news(self):
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = self.state.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"news{timestamp}.txt"
        self.state.filepath = output_dir / filename  # Update this line
        
        async with aiofiles.open(self.state.filepath, "w", encoding="utf-8") as f:
            await f.write(self.state.news)

@app.post("/generate-news")
async def generate_news(request: NewsRequest):
    try:
        news_flow = NewsFlow(language=request.language, topic=request.topic)  # Change theme to topic
        await news_flow.kickoff_async()
        
        if request.format == "pdf":
            # Convert to PDF and stream it
            output_pdf = io.BytesIO()
            converter = PDFConversionTool(
                input_file_path=str(news_flow.state.filepath),
                output_file_path=str(news_flow.state.filepath.with_suffix('.pdf'))
            )
            converter._run()
            
            # Read the PDF file into memory
            with open(news_flow.state.filepath.with_suffix('.pdf'), 'rb') as pdf_file:
                output_pdf.write(pdf_file.read())
            output_pdf.seek(0)
            
            return StreamingResponse(
                output_pdf,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=news_{news_flow.state.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
                }
            )
        
        # Return JSON response for txt format
        return NewsResponse(
            news=news_flow.state.news,
            created_at=news_flow.state.created_at,
            sentence_count=news_flow.state.sentence_count,
            topic=news_flow.state.topic,  # Change theme to topic
            language=news_flow.state.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
