"""
Vision Service - Image understanding, OCR, and document analysis
"""
import base64
from typing import Optional
from services.groq_client import groq_service
import logging

logger = logging.getLogger(__name__)


class VisionService:
    """
    Multi-modal vision capabilities:
    - Image description & understanding
    - OCR (text extraction from images)
    - Document analysis
    - Visual QA
    """

    async def analyze_image(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        model: str = "vision_scout",
        max_tokens: int = 2048,
    ) -> dict:
        """General image analysis"""
        return await groq_service.vision_analysis(
            prompt=prompt,
            image_base64=image_base64,
            image_url=image_url,
            model=model,
            max_tokens=max_tokens,
        )

    async def extract_text_ocr(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """Extract text from image (OCR)"""
        prompt = (
            "Extract ALL text from this image. Return the exact text as it appears, "
            "preserving formatting, line breaks, and structure. If there are tables, "
            "represent them clearly. Only return the extracted text, nothing else."
        )
        return await self.analyze_image(
            prompt=prompt,
            image_base64=image_base64,
            image_url=image_url,
            model="vision_scout",
            max_tokens=4096,
        )

    async def analyze_document(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        analysis_type: str = "summary",
    ) -> dict:
        """Analyze a document image"""
        prompts = {
            "summary": "Analyze this document image. Provide a comprehensive summary of its contents, key points, and any notable information.",
            "extract": "Extract all structured information from this document. Include headers, body text, dates, numbers, names, and any other data points.",
            "classify": "Classify this document. What type of document is it? (invoice, receipt, letter, form, report, etc.) Provide the classification and key metadata.",
            "translate": "Extract all text from this document and translate it to English. Preserve the document structure.",
        }

        prompt = prompts.get(analysis_type, prompts["summary"])
        return await self.analyze_image(
            prompt=prompt,
            image_base64=image_base64,
            image_url=image_url,
            model="vision_maverick",
            max_tokens=4096,
        )

    async def compare_images(
        self,
        images_base64: list,
        prompt: str = "Compare these images and describe the differences and similarities.",
    ) -> dict:
        """Compare multiple images (sends first image, describes comparison)"""
        if not images_base64:
            return {"content": "No images provided", "latency_ms": 0, "model": ""}

        # For now, analyze each separately and combine
        results = []
        for i, img in enumerate(images_base64[:4]):  # Max 4 images
            result = await self.analyze_image(
                prompt=f"Describe image {i+1} in detail for comparison purposes.",
                image_base64=img,
                model="vision_scout",
            )
            results.append(f"Image {i+1}: {result['content']}")

        # Synthesize comparison
        comparison_prompt = f"""Based on these descriptions, {prompt}

{chr(10).join(results)}"""

        from services.groq_client import groq_service
        comparison = await groq_service.chat_completion(
            messages=[{"role": "user", "content": comparison_prompt}],
            model="general",
        )

        return comparison


# Singleton
vision_service = VisionService()