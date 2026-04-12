from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from src.core.pipeline import CognitivePipeline

app = FastAPI(
    title="AlphaEdge Cognitive API", 
    description="Zero Cost, TurboQuant Edge AI Loop", 
    version="1.0"
)

# Lazy initialization to support fast server startup and handle missing offline models gracefully
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            _pipeline = CognitivePipeline()
        except Exception as e:
            # If models not downloaded, it throws FileNotFoundError
            raise HTTPException(status_code=500, detail=f"Engine initialization failed: {e}")
    return _pipeline

class ThinkRequest(BaseModel):
    query: str

class ThinkResponse(BaseModel):
    original_query: str
    draft: str
    critique: str
    final_synthesis: str

@app.post("/api/v1/think", response_model=ThinkResponse)
def think(request: ThinkRequest):
    pipeline = get_pipeline()
    state = pipeline.run(request.query)
    
    return ThinkResponse(
        original_query=state.original_prompt,
        draft=state.generator_draft or "",
        critique=state.challenger_critique or "",
        final_synthesis=state.synthesized_result or ""
    )

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
