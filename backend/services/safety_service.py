"""
Safety Service - Content moderation, prompt injection detection, and safety guardrails
"""
from typing import Dict, List, Optional
from services.groq_client import groq_service
import logging

logger = logging.getLogger(__name__)


class SafetyService:
    """
    Multi-layer safety system:
    1. Llama Guard 4 - Content moderation
    2. Prompt Guard - Injection detection
    3. GPT-OSS Safeguard - Nuanced reasoning about borderline content
    """

    async def full_safety_check(self, content: str) -> dict:
        """Run all safety checks on content"""
        results = {
            "is_safe": True,
            "checks": {},
            "details": [],
        }

        # 1. Content Moderation (Llama Guard 4)
        try:
            guard_result = await groq_service.check_safety(
                content=content,
                model="guard",
            )
            results["checks"]["content_moderation"] = {
                "is_safe": guard_result["is_safe"],
                "details": guard_result["details"],
                "latency_ms": guard_result["latency_ms"],
            }
            if not guard_result["is_safe"]:
                results["is_safe"] = False
                results["details"].append(
                    f"Content moderation flag: {guard_result['details']}"
                )
        except Exception as e:
            logger.warning(f"Guard check failed: {e}")
            results["checks"]["content_moderation"] = {
                "is_safe": True,
                "details": f"Check failed: {str(e)}",
                "latency_ms": 0,
            }

        # 2. Prompt Injection Detection
        try:
            injection_result = await self._check_prompt_injection(content)
            results["checks"]["prompt_injection"] = injection_result
            if not injection_result["is_safe"]:
                results["is_safe"] = False
                results["details"].append(
                    f"Prompt injection detected: {injection_result['details']}"
                )
        except Exception as e:
            logger.warning(f"Injection check failed: {e}")
            results["checks"]["prompt_injection"] = {
                "is_safe": True,
                "details": f"Check failed: {str(e)}",
                "latency_ms": 0,
            }

        return results

    async def _check_prompt_injection(self, content: str) -> dict:
        """Check for prompt injection attempts"""
        result = await groq_service.check_safety(
            content=content,
            model="prompt_guard",
        )
        return {
            "is_safe": result["is_safe"],
            "details": result["details"],
            "latency_ms": result["latency_ms"],
        }

    async def moderate_content(self, content: str) -> dict:
        """Quick content moderation check"""
        return await groq_service.check_safety(
            content=content,
            model="guard",
        )

    async def safeguard_reasoning(self, content: str) -> dict:
        """
        Deep safety analysis with reasoning for borderline content.
        Uses GPT-OSS Safeguard for nuanced analysis.
        """
        try:
            result = await groq_service.check_safety(
                content=content,
                model="safeguard",
            )
            return result
        except Exception as e:
            logger.warning(f"Safeguard reasoning failed: {e}")
            # Fall back to basic guard
            return await self.moderate_content(content)

    async def check_and_filter(
        self,
        user_input: str,
        ai_response: str,
    ) -> dict:
        """Check both user input and AI response for safety"""
        input_check = await self.moderate_content(user_input)
        response_check = await self.moderate_content(ai_response)

        return {
            "input_safe": input_check["is_safe"],
            "response_safe": response_check["is_safe"],
            "overall_safe": input_check["is_safe"] and response_check["is_safe"],
            "input_details": input_check["details"],
            "response_details": response_check["details"],
        }


# Singleton
safety_service = SafetyService()