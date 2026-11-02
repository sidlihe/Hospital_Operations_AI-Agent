from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.logger import get_logger

logger = get_logger(__name__)

class AgentResponse(BaseModel):
    agent_name: str
    status: str = "success"
    action_taken: str
    details: Dict[str, Any] = Field(default_factory=dict)
    summary_message: str

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.llm = get_llm(temperature=0.1)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            ("human", "{input_text}")
        ])

    async def execute_prompt(self, input_text: str) -> str:
        chain = self.prompt | self.llm
        logger.info("Agent %s started an LLM request", self.name)
        try:
            response = await chain.ainvoke({"input_text": input_text})
        except Exception:
            logger.exception("Agent %s LLM request failed", self.name)
            raise
        return response.content

if __name__ == "__main__":
    import asyncio

    async def main():
        agent = BaseAgent(name="TestAgent", system_prompt="You are a helpful assistant.")
        response = await agent.execute_prompt("Hello, how can you assist me today?")
        print(response)

    asyncio.run(main())