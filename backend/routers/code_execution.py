"""
Code Execution Router - Code generation, execution, and debugging
"""
from fastapi import APIRouter, HTTPException
from models.schemas import CodeRequest, CodeResponse
from services.compound_service import compound_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/code", tags=["Code"])


@router.post("/generate", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """Generate code with optional execution"""
    try:
        result = await compound_service.generate_code(
            prompt=request.prompt,
            language=request.language,
            execute=request.execute,
            model=request.model,
        )
        return CodeResponse(
            code=result["content"],
            explanation="",
            execution_result=None,
            model_used=result["model"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_code(code: str, language: str = "python"):
    """Execute code in sandboxed environment"""
    try:
        result = await compound_service.execute_code(
            code=code,
            language=language,
        )
        return {
            "output": result["content"],
            "tools_used": result.get("tools_used", []),
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug")
async def debug_code(code: str, error: str = "", language: str = "python"):
    """Debug code and get fix suggestions"""
    try:
        prompt = f"""Debug this {language} code:

```{language}
{code}
```"""
        if error:
            prompt += f"\n\nError message: {error}"

        prompt += "\n\nIdentify the bugs, explain what's wrong, and provide the corrected code."

        result = await compound_service.generate_code(
            prompt=prompt,
            language=language,
            model="coding",
        )
        return {
            "analysis": result["content"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain_code(code: str, language: str = "python"):
    """Explain code in detail"""
    try:
        prompt = f"""Explain this {language} code in detail:

```{language}
{code}

Provide:

Overall purpose

Line-by-line explanation

Key concepts used

Potential improvements ```"""


        from services.groq_client import groq_service
        result = await groq_service.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert code explainer. Be clear and thorough."},
                {"role": "user", "content": prompt},
            ],
            model="general",
        )
        return {
            "explanation": result["content"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }

    except Exception as e:
        logger.error(f"Code explain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))