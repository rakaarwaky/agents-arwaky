"""Code execution adapter with input validation and safety checks."""

import logging
import re

from contract import BlenderConnectionPort, CodeExecutionPort
from taxonomy import ActionName, Prompt, SuccessFlag
from taxonomy.blender_mcp_error import ErrorMessage, ValidationError

logger = logging.getLogger("BlenderMCPServer")

# Maximum code length (chars) to prevent abuse
MAX_CODE_LENGTH = 10_000

# Blocked patterns — dangerous system-level operations
# These are checked as regex patterns against the submitted code
BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bos\.system\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.popen\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.exec\w*\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.spawn\w*\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.remove\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.unlink\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.rmdir\s*\(", re.IGNORECASE),
    re.compile(r"\bsubprocess\b", re.IGNORECASE),
    re.compile(r"\bshutil\.rmtree\s*\(", re.IGNORECASE),
    re.compile(r"\bshutil\.move\s*\(", re.IGNORECASE),
    re.compile(r"__import__\s*\("),
    re.compile(r"\bimportlib\b"),
    re.compile(r"\bsocket\s*\.\s*socket\s*\("),
    re.compile(r"\brequests\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"\burllib\b"),
]

# Descriptive names for log messages
BLOCKED_DESCRIPTIONS = [
    "os.system()",
    "os.popen()",
    "os.exec*()",
    "os.spawn*()",
    "os.remove()",
    "os.unlink()",
    "os.rmdir()",
    "subprocess",
    "shutil.rmtree()",
    "shutil.move()",
    "__import__()",
    "importlib",
    "socket.socket()",
    "requests HTTP",
    "urllib",
]


def validate_code(code: str) -> None:
    """Validate code for safety before execution.

    Raises ValidationError if the code contains blocked patterns
    or exceeds length limits.
    """
    if not code or not code.strip():
        raise ValidationError(ErrorMessage("Code cannot be empty"))

    if len(code) > MAX_CODE_LENGTH:
        raise ValidationError(
            ErrorMessage(f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters (received {len(code)})")
        )

    for pattern, description in zip(BLOCKED_PATTERNS, BLOCKED_DESCRIPTIONS, strict=False):
        if pattern.search(code):
            logger.warning(
                "Blocked code execution attempt: pattern '%s' detected",
                description,
            )
            raise ValidationError(
                ErrorMessage(
                    f"Code contains blocked pattern: {description}. "
                    f"For security, system-level operations are not allowed "
                    f"through execute_blender_code. Use Blender's Python API (bpy) instead."
                )
            )


class CodeExecutionAdapter(CodeExecutionPort):
    """Wrapper class for code execution functions with input validation."""

    _success_ref: SuccessFlag = SuccessFlag(True)

    def __init__(self, connection_port: BlenderConnectionPort):
        self._connection_port = connection_port

    async def execute_blender_code(self, code: Prompt) -> Prompt:
        """
        Execute Python code in Blender with safety validation.

        Parameters:
        - code: The Python code to execute (must use bpy API only)

        Raises:
        - ValidationError: If code contains blocked patterns or is too long
        """
        code_str = str(code)

        # Validate input before sending to Blender
        try:
            validate_code(code_str)
        except ValidationError as e:
            logger.warning("Code validation failed: %s", e)
            return Prompt(f"Validation error: {e}")

        # Audit log — record all code execution attempts
        logger.info(
            "Executing Blender code (length=%d chars): %.100s%s",
            len(code_str),
            code_str,
            "..." if len(code_str) > 100 else "",
        )

        try:
            result = self._connection_port.send_command(ActionName("execute_code"), {"code": code_str})
            return Prompt(f"Code executed successfully: {result.get('result', '')}")
        except Exception as e:
            logger.error("Error executing code: %s", e)
            return Prompt(f"Error executing code: {e}")
