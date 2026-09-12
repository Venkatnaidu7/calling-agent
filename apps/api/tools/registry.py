from typing import Any, Callable, Awaitable
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()

@dataclass
class ToolDefinition:
    """A registered tool that the AI can call."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    handler: Callable[..., Awaitable[dict[str, Any]]]  # async function
    requires_confirmation: bool = False  # if True, AI should confirm before executing
    category: str = "general"


class ToolRegistry:
    """Global registry of all available tools."""
    _tools: dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition) -> None:
        cls._tools[tool.name] = tool
        logger.info("tool_registered", name=tool.name, category=tool.category)

    @classmethod
    def get(cls, name: str) -> ToolDefinition | None:
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> dict[str, ToolDefinition]:
        return cls._tools.copy()

    @classmethod
    def get_openai_tools(cls, permitted_tools: dict[str, bool]) -> list[dict[str, Any]]:
        """Get OpenAI function definitions for tools that the agent has permission to use."""
        tools = []
        for name, tool in cls._tools.items():
            if permitted_tools.get(name, False):
                tools.append({
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                })
        return tools

    @classmethod
    def list_tool_names(cls) -> list[str]:
        return list(cls._tools.keys())
