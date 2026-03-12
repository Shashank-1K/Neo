"""
Structured Output Service - Extract structured data from any content
"""
from typing import Dict, List, Optional
from services.groq_client import groq_service
import json
import logging

logger = logging.getLogger(__name__)


class StructuredOutputService:
    """
    Extract structured data using JSON Schema enforcement.
    Guaranteed type-safe outputs from any content.
    """

    # Pre-built schemas for common use cases
    SCHEMAS = {
        "contact": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"},
                "role": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "invoice": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "date": {"type": "string"},
                "due_date": {"type": "string"},
                "vendor": {"type": "string"},
                "total_amount": {"type": "number"},
                "currency": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                            "total": {"type": "number"},
                        },
                        "required": ["description", "total"],
                        "additionalProperties": False,
                    }
                },
                "tax": {"type": "number"},
                "subtotal": {"type": "number"},
            },
            "required": ["invoice_number", "total_amount"],
            "additionalProperties": False,
        },
        "meeting_notes": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "date": {"type": "string"},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "summary": {"type": "string"},
                "action_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "assignee": {"type": "string"},
                            "deadline": {"type": "string"},
                        },
                        "required": ["task"],
                        "additionalProperties": False,
                    }
                },
                "decisions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "next_meeting": {"type": "string"},
            },
            "required": ["title", "summary"],
            "additionalProperties": False,
        },
        "sentiment": {
            "type": "object",
            "properties": {
                "overall_sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "mixed"]
                },
                "confidence": {"type": "number"},
                "emotions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "key_phrases": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "summary": {"type": "string"},
            },
            "required": ["overall_sentiment", "confidence"],
            "additionalProperties": False,
        },
        "todo_list": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "category": {"type": "string"},
                            "estimated_time": {"type": "string"},
                        },
                        "required": ["title", "priority"],
                        "additionalProperties": False,
                    }
                }
            },
            "required": ["tasks"],
            "additionalProperties": False,
        },
    }

    async def extract(
        self,
        content: str,
        schema: Dict,
        model: str = "general",
        instructions: str = "",
    ) -> dict:
        """Extract structured data from content using a JSON schema"""
        system_msg = "Extract the requested structured data from the provided content. Be accurate and thorough."
        if instructions:
            system_msg += f"\n\nAdditional instructions: {instructions}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": content},
        ]

        return await groq_service.structured_completion(
            messages=messages,
            json_schema=schema,
            model=model,
        )

    async def extract_with_preset(
        self,
        content: str,
        preset: str,
        model: str = "general",
    ) -> dict:
        """Extract data using a pre-built schema preset"""
        if preset not in self.SCHEMAS:
            available = ", ".join(self.SCHEMAS.keys())
            raise ValueError(f"Unknown preset: {preset}. Available: {available}")

        return await self.extract(
            content=content,
            schema=self.SCHEMAS[preset],
            model=model,
        )

    async def extract_from_image(
        self,
        image_base64: str,
        schema: Dict,
        prompt: str = "Extract structured data from this image",
    ) -> dict:
        """Extract structured data from an image"""
        # First, get text from image using vision
        from services.vision_service import vision_service
        vision_result = await vision_service.extract_text_ocr(
            image_base64=image_base64,
        )

        # Then extract structured data from the text
        return await self.extract(
            content=vision_result["content"],
            schema=schema,
        )

    def get_available_presets(self) -> dict:
        """Get all available preset schemas"""
        return {
            name: {
                "schema": schema,
                "description": self._describe_schema(schema),
            }
            for name, schema in self.SCHEMAS.items()
        }

    def _describe_schema(self, schema: dict) -> str:
        """Generate a human-readable description of a schema"""
        if "properties" in schema:
            fields = list(schema["properties"].keys())
            required = schema.get("required", [])
            return f"Fields: {', '.join(fields)}. Required: {', '.join(required)}"
        return "Complex schema"


# Singleton
structured_service = StructuredOutputService()