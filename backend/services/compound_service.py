"""
Compound Service - Agentic AI with built-in tools
"""
from typing import Optional, List, Dict
from services.groq_client import groq_service
import logging

logger = logging.getLogger(__name__)


class CompoundService:
    """
    Groq Compound AI System capabilities:
    - Web Search (live internet search)
    - Visit Website (fetch and read URLs)
    - Browser Automation (parallel browser control)
    - Code Execution (sandboxed Python)
    - Wolfram Alpha (math/science computation)
    """

    async def research(
        self,
        query: str,
        context: str = "",
        model: str = "compound",
        max_tokens: int = 8192,
    ) -> dict:
        """Research a topic using web search and browser automation"""
        system_msg = (
            "You are a research assistant with access to web search, "
            "browser automation, and other tools. Provide comprehensive, "
            "well-sourced research with citations. Be thorough and accurate."
        )

        messages = [
            {"role": "system", "content": system_msg},
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context: {context}"
            })

        messages.append({"role": "user", "content": query})

        return await groq_service.compound_query(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        explanation_request: str = "",
    ) -> dict:
        """Execute code using Compound's sandboxed execution"""
        prompt = f"""Execute the following {language} code and show the output:

```{language}
{code}
```"""

        if explanation_request:
            prompt += f"\n\nAlso: {explanation_request}"

        messages = [
            {
                "role": "system",
                "content": "You are a code execution assistant. Run the provided code and show results. If there are errors, explain them and suggest fixes."
            },
            {"role": "user", "content": prompt}
        ]

        return await groq_service.compound_query(
            messages=messages,
            model="compound",
        )

    async def math_compute(
        self,
        query: str,
        show_steps: bool = True,
    ) -> dict:
        """Math and science computation using Wolfram Alpha"""
        prompt = query
        if show_steps:
            prompt += "\n\nShow detailed step-by-step solution."

        messages = [
            {
                "role": "system",
                "content": "You are a math and science expert. Use Wolfram Alpha and other computation tools to solve problems accurately. Show your work and explain each step."
            },
            {"role": "user", "content": prompt}
        ]

        return await groq_service.compound_query(
            messages=messages,
            model="compound",
        )

    async def visit_website(
        self,
        url: str,
        task: str = "Summarize the content of this webpage",
    ) -> dict:
        """Visit and analyze a website"""
        messages = [
            {
                "role": "system",
                "content": "You are a web analysis assistant. Visit the provided URL and complete the requested task."
            },
            {
                "role": "user",
                "content": f"Visit this URL: {url}\n\nTask: {task}"
            }
        ]

        return await groq_service.compound_query(
            messages=messages,
            model="compound",
        )

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        execute: bool = False,
        model: str = "coding",
    ) -> dict:
        """Generate code with optional execution"""
        system_msg = f"""You are an expert {language} programmer. Write clean, 
well-documented, production-quality code. Include error handling and type hints where appropriate."""

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

        if execute:
            # Use Compound for code generation + execution
            messages[0]["content"] += " After generating the code, execute it and show the output."
            return await groq_service.compound_query(
                messages=messages,
                model="compound",
            )
        else:
            # Use specialized coding model
            result = await groq_service.chat_completion(
                messages=messages,
                model=model,
                temperature=0.3,
                max_tokens=4096,
            )
            return result

    async def multi_step_agent(
        self,
        task: str,
        steps: Optional[List[str]] = None,
    ) -> dict:
        """Execute a multi-step agentic task"""
        if steps:
            step_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            prompt = f"""Complete the following task step by step:

Task: {task}

Steps to follow:
{step_text}

Execute each step using available tools (web search, code execution, 
browser automation, Wolfram Alpha) as needed. Report results for each step."""
        else:
            prompt = f"""Complete the following task. Break it down into logical steps 
and use available tools (web search, code execution, browser automation, 
Wolfram Alpha) as needed.

Task: {task}"""

        messages = [
            {
                "role": "system",
                "content": "You are an advanced AI agent capable of breaking down complex tasks and using tools to accomplish them. Be thorough and report your progress."
            },
            {"role": "user", "content": prompt}
        ]

        return await groq_service.compound_query(
            messages=messages,
            model="compound",
            max_tokens=8192,
        )


# Singleton
compound_service = CompoundService()