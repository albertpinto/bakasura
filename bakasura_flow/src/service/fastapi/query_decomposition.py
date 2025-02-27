from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import os
from enum import Enum
import logging
import re
import asyncio
import aiohttp
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from instructor import patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Query Decomposition API",
    description="API for decomposing queries using various LLM providers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModelType(Enum):
    GROQ = "groq"
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"

class LLMConfig(BaseModel):
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    api_key: Optional[str] = Field(None)

class DecomposedQuestion(BaseModel):
    question: str
    topics: List[str] = []

class DecompositionRequest(BaseModel):
    query: str
    config: LLMConfig

class DecompositionResponse(BaseModel):
    original_query: str
    decomposed_questions: List[DecomposedQuestion]
    model_used: str

# Update the supported models configuration
class ModelConfig:
    SUPPORTED_MODELS = {
        "groq": ["llama-3.3-70b-versatile"],  # Updated to use exact model name
        "openai": ["gpt-4-turbo", "gpt-3.5-turbo"],
        "claude": ["claude-2", "claude-instant"],
        "ollama": ["llama2", "mistral"]
    }

class QueryDecomposer:
    def __init__(self, model: str, temperature: float = 0.7, api_key: Optional[str] = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.model_type = self._determine_model_type()
        self._validate_api_key()

    def _determine_model_type(self) -> ModelType:
        """Determine the model type based on the model name"""
        model_lower = self.model.lower()
        
        # Handle Groq's specific model name
        if model_lower == "llama-3.3-70b-versatile" or model_lower.startswith("groq"):
            return ModelType.GROQ
        elif model_lower.startswith(("gpt-", "text-")):
            return ModelType.OPENAI
        elif model_lower.startswith("claude"):
            return ModelType.CLAUDE
        else:
            return ModelType.OLLAMA        


    def _validate_api_key(self):
        """Validate and set API key based on model type"""
        if self.model_type != ModelType.OLLAMA:
            if not self.api_key:
                env_var_map = {
                    ModelType.GROQ: "GROQ_API_KEY",
                    ModelType.OPENAI: "OPENAI_API_KEY",
                    ModelType.CLAUDE: "ANTHROPIC_API_KEY"
                    
                }
                env_var = env_var_map[self.model_type]
                self.api_key = os.getenv(env_var)
                if not self.api_key:
                    raise ValueError(f"{env_var} must be provided")

    def _build_prompt(self, query: str) -> str:
        """Build the prompt template with more explicit formatting instructions"""
        return f'''# Context
You are a chess expert helping to generate clear, well-formed questions about chess topics.

# Task
Original topic: {query}

Generate 5 alternative questions about this chess topic. Each question should:
1. Start with words like "What", "How", "Why", "Which", "Can"
2. End with a question mark
3. Be specific and detailed
4. Focus on different aspects (opening theory, practical play, historical development, modern usage, key ideas)

# Output Format
Return a JSON array of strings, with each string being a properly formatted question. For example:
[
    "What are the key strategic ideas in the Sicilian Dragon variation?",
    "How do modern grandmasters approach the Dragon variation in tournament play?",
    "Which common tactical patterns should players know in the Dragon Sicilian?",
    "What are the most critical lines in the Accelerated Dragon variation?",
    "How has the theory of the Dragon Sicilian evolved in recent years?"
]
'''

    def _parse_response(self, response: str) -> List[str]:
        """Parse the LLM response into a list of questions"""
        try:
            # Clean up the response
            response = response.strip()
            
            # First try to parse as JSON
            try:
                if response.startswith('[') and response.endswith(']'):
                    questions = json.loads(response)
                    if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
                        return questions
            except json.JSONDecodeError:
                pass

            # Fall back to line-by-line parsing
            questions = []
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove common list markers
                line = re.sub(r'^\d+\.\s*', '', line)  # Remove "1. "
                line = re.sub(r'^\-\s*', '', line)     # Remove "- "
                line = re.sub(r'^\*\s*', '', line)     # Remove "* "
                
                # Clean up the question
                cleaned = self._clean_question(line)
                if cleaned:
                    questions.append(cleaned)

            return questions if questions else []

        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            raise ValueError(f"Failed to parse response: {str(e)}")

    async def _get_model_response(self, prompt: str) -> str:
        """Get response from the selected model with proper async handling and retries"""
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if self.model_type == ModelType.GROQ:
                    client = patch(Groq(api_key=self.api_key))
                    chat_completion = client.chat.completions.create(
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        model="llama-3.3-70b-versatile",
                        max_retries=3,
                        temperature=self.temperature,
                        max_tokens=1000,
                        top_p=0.9
                    )
                    response = chat_completion.choices[0].message.content
                    logger.info(f"Raw Groq response: {response}")
                    return response

                elif self.model_type == ModelType.OPENAI:
                    client = patch(AsyncOpenAI(api_key=self.api_key))
                    response = await client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_retries=3,
                        temperature=self.temperature,
                        max_tokens=1000
                    )
                    return response.choices[0].message.content

                elif self.model_type == ModelType.CLAUDE:
                    client = patch(AsyncAnthropic(api_key=self.api_key))
                    response = await client.messages.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_retries=3,
                        max_tokens=1000
                    )
                    return response.content[0].text

                else:  # OLLAMA
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": self.model,
                                "prompt": prompt,
                                "temperature": self.temperature
                            },
                            timeout=30.0
                        ) as response:
                            if response.status != 200:
                                text = await response.text()
                                raise HTTPException(
                                    status_code=response.status,
                                    detail=f"Ollama API error: {text}"
                                )
                            data = await response.json()
                            return data["response"]

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(f"Retry {retry_count} after error: {str(e)}")
                    await asyncio.sleep(1)  # Wait before retrying
                    continue
                logger.error(f"Model response error after {retry_count} retries: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error getting model response: {str(e)}"
                )

    def _clean_question(self, question: str) -> str:
        """Clean and validate a question with more lenient validation"""
        if not question:
            return ""
            
        # Basic cleaning
        question = question.strip()
        question = ' '.join(question.split())  # Normalize whitespace
        
        # Remove any markdown or list formatting
        question = re.sub(r'^[-*\d.)\]]?\s*', '', question)
        
        # Ensure it ends with a question mark
        if not question.endswith('?'):
            question += '?'
        
        # More lenient validation for question structure
        question_starters = [
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 
            'can', 'could', 'is', 'are', 'does', 'do', 'should', 
            'has', 'have', 'will', 'would'
        ]
        
        # Check if it starts with a question word or contains chess-related terms
        chess_terms = ['sicilian', 'dragon', 'opening', 'variation', 'defense', 'attack', 
                    'position', 'game', 'move', 'player', 'strategy', 'tactic']
                    
        is_valid = (
            any(question.lower().startswith(starter) for starter in question_starters) or
            any(term in question.lower() for term in chess_terms)
        )
        
        return question if is_valid else ""

    def _extract_topics(self, question: str) -> List[str]:
        """Extract chess-related topics from the question"""
        chess_topics = {
            'opening': ['opening', 'variation', 'gambit', 'defense', 'sicilian', 'ruy lopez'],
            'middlegame': ['middlegame', 'position', 'attack', 'strategy'],
            'endgame': ['endgame', 'ending', 'mate', 'checkmate'],
            'players': ['player', 'grandmaster', 'champion', 'carlsen', 'kasparov'],
            'competition': ['tournament', 'championship', 'match', 'competition'],
            'analysis': ['analysis', 'evaluation', 'engine', 'computer', 'theory']
        }
        
        found_topics = set()
        question_lower = question.lower()
        
        for main_topic, subtopics in chess_topics.items():
            if any(subtopic in question_lower for subtopic in subtopics):
                found_topics.add(main_topic)
                
        return list(found_topics)[:3]

    async def decompose(self, query: str) -> List[DecomposedQuestion]:
        """Main method to decompose a query into multiple questions"""
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        try:
            prompt = self._build_prompt(query)
            response_text = await self._get_model_response(prompt)
            questions = self._parse_response(response_text)
            
            decomposed_questions = []
            for q in questions:
                cleaned_q = self._clean_question(q)
                if cleaned_q:
                    topics = self._extract_topics(cleaned_q)
                    decomposed_questions.append(
                        DecomposedQuestion(question=cleaned_q, topics=topics)
                    )
            
            if not decomposed_questions:
                raise ValueError("No valid questions generated")
                
            return decomposed_questions

        except Exception as e:
            logger.error(f"Decomposition error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decompose query: {str(e)}"
            )

@app.post("/decompose", response_model=DecompositionResponse)
async def decompose_query(request: DecompositionRequest):
    """Endpoint to decompose a query into multiple questions"""
    try:
        decomposer = QueryDecomposer(
            model=request.config.model,
            temperature=request.config.temperature,
            api_key=request.config.api_key
        )
        
        questions = await decomposer.decompose(request.query)
        
        return DecompositionResponse(
            original_query=request.query,
            decomposed_questions=questions,
            model_used=request.config.model
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/models")
async def list_supported_models():
    """List all supported model types"""
    return {"supported_models": ModelConfig.SUPPORTED_MODELS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)