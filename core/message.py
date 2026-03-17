from typing import Literal, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

MessageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):
    """消息类"""
    content: str
    role: MessageRole
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def __init__(self, role: MessageRole, content: str, **kwargs):
        super().__init__(
            content=content,
            role=role,
            timestamp=kwargs.get('timestamp', datetime.now()),
            metadata=kwargs.get('metadata', {})
        )

        def to_dict(self) -> Dict[str, Any]:
            return {
                "content": self.content,
                "role": self.role,
            }

        def __str__(self) -> str:
            return f"{self.role}: {self.content}"

    