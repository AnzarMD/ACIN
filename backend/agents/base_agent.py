import os
"""Base agent class with Bedrock LLM configuration."""

import json
from langchain_aws import ChatBedrock


class BaseAgent:
    """Base class for all ACIN agents using Claude Sonnet on Bedrock."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 2048, "temperature": 0.1, "top_p": 0.9},
        )

    async def invoke_json(self, messages: list) -> dict:
        """Invoke LLM and parse JSON response."""
        response = await self.llm.ainvoke(messages)
        content = response.content

        # Strip JSON fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(content)

