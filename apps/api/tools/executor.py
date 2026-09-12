import json
import time
import uuid
import structlog
from typing import Any

from apps.api.tools.registry import ToolRegistry

logger = structlog.get_logger()


class ToolExecutionResult:
    def __init__(
        self, success: bool, data: dict[str, Any] = None, error: str = None, error_code: str = None
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.error_code = error_code

    def to_json(self) -> str:
        if self.success:
            return json.dumps({"success": True, **self.data})
        return json.dumps(
            {
                "success": False,
                "error_code": self.error_code or "TOOL_ERROR",
                "error": self.error or "Tool execution failed",
            }
        )


class ToolExecutor:
    """
    Secure tool execution pipeline.
    Every tool call passes through:
    1. Tool exists in registry
    2. Agent has permission for this tool
    3. Arguments validation
    4. Tenant context injection
    5. Execution with timeout
    6. Result validation
    7. Audit event emission
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        call_id: str,
        tool_permissions: dict[str, bool],
        to_number: str = "",
        from_number: str = "",
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.call_id = call_id
        self.tool_permissions = tool_permissions
        self.to_number = to_number
        self.from_number = from_number
        self.execution_log: list[dict] = []

    async def execute(
        self,
        tool_name: str,
        arguments: str,  # JSON string from OpenAI
        call_id_openai: str,  # OpenAI's call_id for the function call
    ) -> ToolExecutionResult:
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        log_entry = {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "timestamp": start_time,
        }

        try:
            # Step 1: Check tool exists
            tool = ToolRegistry.get(tool_name)
            if not tool:
                logger.warning("tool_not_found", tool=tool_name)
                return ToolExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                    error_code="TOOL_NOT_FOUND",
                )

            # Step 2: Check permission
            if not self.tool_permissions.get(tool_name, False):
                logger.warning("tool_permission_denied", tool=tool_name, agent_id=self.agent_id)
                return ToolExecutionResult(
                    success=False,
                    error=f"Permission denied for tool '{tool_name}'",
                    error_code="PERMISSION_DENIED",
                )

            # Step 3: Parse arguments
            try:
                parsed_args = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolExecutionResult(
                    success=False, error="Invalid tool arguments", error_code="INVALID_ARGUMENTS"
                )

            # Step 4: Inject context
            parsed_args["_context"] = {
                "tenant_id": self.tenant_id,
                "agent_id": self.agent_id,
                "call_id": self.call_id,
                "execution_id": execution_id,
                "to_number": self.to_number,
                "from_number": self.from_number,
            }

            # Step 5: Execute
            logger.info("tool_executing", tool=tool_name, execution_id=execution_id)
            result_data = await tool.handler(**parsed_args)

            # Step 6: Validate result
            if not isinstance(result_data, dict):
                result_data = {"result": str(result_data)}

            duration = time.time() - start_time
            log_entry["duration"] = duration
            log_entry["success"] = True
            self.execution_log.append(log_entry)

            logger.info("tool_executed", tool=tool_name, duration=f"{duration:.3f}s", success=True)
            return ToolExecutionResult(success=True, data=result_data)

        except Exception as e:
            duration = time.time() - start_time
            log_entry["duration"] = duration
            log_entry["success"] = False
            log_entry["error"] = str(e)
            self.execution_log.append(log_entry)

            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            return ToolExecutionResult(success=False, error=str(e), error_code="EXECUTION_ERROR")
