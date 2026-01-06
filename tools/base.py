"""
Base Tool class for Agno Agent
All tools inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Tool(ABC):
    """Base class for all tools"""
    
    def __init__(self):
        self.name: str = "base_tool"
        self.description: str = "Base tool description"
    
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Returns:
            Dictionary containing the tool's output
        """
        pass
    
    def get_info(self) -> Dict[str, str]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description
        }
    
    def __repr__(self) -> str:
        return f"Tool(name='{self.name}')"


class ToolRegistry:
    """Registry to manage all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> list:
        """List all registered tools"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def __contains__(self, name: str) -> bool:
        return name in self.tools

