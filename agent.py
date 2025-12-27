# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maxim Strekolovskiy

import os
import json
import logging
from typing import List, Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='w'
)

class ChatGPTClassifier:
    """Chat message classifier using the OpenAI API.

    This project is intentionally generic and uses a neutral taxonomy
    suitable for customer support / sales / product analytics.
    """
    
    CATEGORIES = [
        "Pricing",
        "Billing & Payments",
        "Refunds & Cancellations",
        "Account & Login",
        "Onboarding & Setup",
        "Product Features",
        "Integrations",
        "Data Export & Reports",
        "Technical Support",
        "Bug Report",
        "Feature Request",
        "Performance",
        "Security & Privacy",
        "Sales Inquiry",
        "Partnerships",
        "Feedback",
        "Complaint",
        "Praise",
        "General Question",
        "Other"
    ]

    SYSTEM_PROMPT = f"""You are a customer support and analytics specialist.
Classify each message using these strict rules:

1) Category MUST be from this list (English only):
{CATEGORIES}

2) Sentiment MUST be one of:
- positive (gratitude, praise, positive emotions)
- negative (complaints, criticism, irritation)
- neutral (all other cases)

3) Output format MUST be JSON exactly:
{{"category": "selected_category", "sentiment": "positive|negative|neutral"}}

Examples:

=== Positive ===
Text: "Thanks! Your team was super helpful."
Answer: {{"category": "Praise", "sentiment": "positive"}}

Text: "Great product, really enjoying the new dashboard."
Answer: {{"category": "Product Features", "sentiment": "positive"}}

=== Negative ===
Text: "Why are you responding so slowly? This is unacceptable."
Answer: {{"category": "Complaint", "sentiment": "negative"}}

Text: "I can't log in after the update. This is broken."
Answer: {{"category": "Account & Login", "sentiment": "negative"}}

=== Neutral ===
Text: "How much does the Pro plan cost?"
Answer: {{"category": "Pricing", "sentiment": "neutral"}}

Text: "Do you integrate with Slack?"
Answer: {{"category": "Integrations", "sentiment": "neutral"}}

=== Special Cases ===
Text: "Hi! How are you?"
Answer: {{"category": "Other", "sentiment": "neutral"}}"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in your environment or pass it explicitly."
            )

        # Optional custom base URL (e.g., proxy / gateway). Defaults to the official OpenAI API.
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url) if base_url else AsyncOpenAI(api_key=api_key)

        # Project-wide requirement: use gpt-5-nano for all model invocations.
        self.model = "gpt-5-nano"

    def _build_single_message(self, text: str) -> List[Dict]:
        return [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT
            },
            {
                "role": "user", 
                "content": f"Text to analyze:\n{text}\n\nJSON:"
            }
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def analyze_text(self, text: str) -> Optional[Dict]:
        """Analyze a single text message and return the classification."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self._build_single_message(text),
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500,
                timeout=30.0
            )
            # Log raw response for debugging
            logger.debug(f"Raw API response: {response.choices[0].message.content}")
            
            return self._parse_single_response(response)
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            return None

    def _parse_single_response(self, response) -> Dict:
        try:
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            # Category validation
            category = result.get("category", "Other")
            if category not in self.CATEGORIES:
                logger.warning(f"Invalid category detected: {category}")
                category = "Other"
                
            # Sentiment validation
            sentiment = str(result.get("sentiment", "neutral")).lower().strip()
            if sentiment not in ["positive", "negative", "neutral"]:
                sentiment = "neutral"
                
            return {
                "category": category,
                "sentiment": sentiment
            }
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {content}")
            return {"category": "Other", "sentiment": "neutral"}
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return {"category": "Other", "sentiment": "neutral"}