"""
MCP 编排层（Orchestrator）
负责通过 HTTP API 调用 MCP 服务
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# MCP HTTP Server 地址
MCP_SERVER_URL = "http://localhost:8001"


class MCPToolOrchestrator:
    """MCP 工具编排器，通过 HTTP API 调用 MCP 服务"""
    
    def __init__(self):
        """初始化编排器"""
        # 所有工具都通过 MCP HTTP API 调用
        self.mcp_tools = [
            "get_student_quiz_history",
            "get_wrong_questions_by_subsection",
            "get_student_learning_progress",
            "get_next_content",
            "get_student_weak_points",
            "search_course_content",
            "generate_interactive_quiz",
            "fetch_learning_data",
            "fetch_wrong_questions",
            "fetch_weak_knowledge_points"
        ]
        
        logger.info(f"MCP Tool Orchestrator initialized with {len(self.mcp_tools)} tools")
        logger.info(f"MCP Server URL: {MCP_SERVER_URL}")
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Any:
        """
        执行工具调用（通过 HTTP API）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            db: 数据库会话（MCP 模式下不使用）
            
        Returns:
            工具执行结果
        """
        logger.info(f"MCP Orchestrator executing tool: {tool_name}")
        
        # 通过 HTTP API 调用 MCP Server
        result = self._call_mcp_http(tool_name, arguments)
        
        logger.info(f"Tool {tool_name} executed successfully via MCP HTTP")
        return result
    
    def _call_mcp_http(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        通过 HTTP API 调用 MCP Server
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        logger.info(f"Calling MCP HTTP API: {tool_name}")
        
        try:
            # 构造请求
            request_data = {
                "name": tool_name,
                "arguments": arguments
            }
            
            # 每次创建新的客户端，避免连接池问题
            with httpx.Client(timeout=30.0) as client:
                # 发送 HTTP POST 请求
                response = client.post(
                    f"{MCP_SERVER_URL}/call",
                    json=request_data
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    raise Exception(f"MCP Server returned status {response.status_code}")
                
                # 解析响应
                result = response.json()
                
                # 检查是否成功
                if not result.get("success"):
                    error = result.get("error", "Unknown error")
                    raise Exception(f"MCP tool call failed: {error}")
                
                return result.get("result")
            
        except httpx.ConnectError:
            logger.error("Cannot connect to MCP Server. Is it running on port 8001?")
            raise Exception("MCP Server is not available. Please start MCP HTTP Server first.")
        except Exception as e:
            logger.error(f"MCP HTTP call failed: {e}", exc_info=True)
            raise Exception(f"MCP service error: {str(e)}")


# 创建全局 MCP 编排器实例
mcp_orchestrator = MCPToolOrchestrator()
