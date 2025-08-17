"""Type definitions for Gemini provider integration.

Based on the Gemini API v1beta specification and testing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict, List, Optional, Literal, Any, Dict
from datetime import datetime


# Role types
Role = Literal["user", "model", "system"]

# Finish reasons
class FinishReason(str, Enum):
    """Reasons why generation stopped."""
    STOP = "STOP"
    MAX_TOKENS = "MAX_TOKENS"
    SAFETY = "SAFETY"
    RECITATION = "RECITATION"
    OTHER = "OTHER"


# Safety categories
class HarmCategory(str, Enum):
    """Safety harm categories."""
    HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
    HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
    HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
    HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"


# Safety probability levels
class HarmProbability(str, Enum):
    """Probability levels for harm categories."""
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Request types
class TextPart(TypedDict):
    """Text content part."""
    text: str


class InlineDataPart(TypedDict, total=False):
    """Inline data part for images, etc."""
    inline_data: Dict[str, Any]


Part = TextPart | InlineDataPart


class Content(TypedDict):
    """Content block in request/response."""
    parts: List[Part]
    role: Optional[Role]


class GenerationConfig(TypedDict, total=False):
    """Configuration for text generation."""
    temperature: float
    topP: float
    topK: int
    maxOutputTokens: int
    stopSequences: List[str]
    candidateCount: int


class SafetyRating(TypedDict):
    """Safety rating for content."""
    category: str
    probability: str


class SafetySetting(TypedDict):
    """Safety threshold setting."""
    category: str
    threshold: str


class GeminiRequest(TypedDict, total=False):
    """Request to Gemini API."""
    contents: List[Content]
    generationConfig: Optional[GenerationConfig]
    safetySettings: Optional[List[SafetySetting]]


# Response types
class Candidate(TypedDict):
    """Response candidate."""
    content: Content
    finishReason: str
    index: int
    safetyRatings: List[SafetyRating]


class PromptFeedback(TypedDict, total=False):
    """Feedback about the prompt."""
    safetyRatings: List[SafetyRating]
    blockReason: Optional[str]


class GeminiResponse(TypedDict):
    """Response from Gemini API."""
    candidates: List[Candidate]
    promptFeedback: Optional[PromptFeedback]


# Streaming response
class StreamChunk(TypedDict):
    """A chunk in streaming response."""
    candidates: List[Candidate]
    promptFeedback: Optional[PromptFeedback]


# Model information
class Model(TypedDict):
    """Model information."""
    name: str
    version: str
    displayName: str
    description: str
    inputTokenLimit: int
    outputTokenLimit: int
    supportedGenerationMethods: List[str]
    temperature: float
    topP: float
    topK: int


# Session tracking
@dataclass
class GeminiSession:
    """Track a Gemini conversation session."""
    session_id: str
    started_at: datetime
    model: str = "gemini-pro"
    messages: List[Content] = field(default_factory=list)
    generation_config: Optional[GenerationConfig] = None
    omnara_agent_instance_id: Optional[str] = None
    
    def add_user_message(self, text: str) -> None:
        """Add a user message to the session."""
        self.messages.append({
            "role": "user",
            "parts": [{"text": text}]
        })
    
    def add_model_message(self, text: str) -> None:
        """Add a model response to the session."""
        self.messages.append({
            "role": "model",
            "parts": [{"text": text}]
        })
    
    def get_request_contents(self) -> List[Content]:
        """Get contents formatted for API request."""
        return self.messages


# Intercepted message for Omnara
@dataclass
class InterceptedMessage:
    """Message intercepted by the proxy."""
    timestamp: datetime
    session_id: str
    role: Role
    content: str
    request_data: Optional[GeminiRequest] = None
    response_data: Optional[GeminiResponse] = None
    is_streaming: bool = False
    metadata: Optional[Dict[str, Any]] = None


# Proxy configuration
@dataclass
class ProxyConfig:
    """Configuration for the Gemini proxy."""
    listen_port: int = 8080
    target_host: str = "generativelanguage.googleapis.com"
    omnara_api_key: str = ""
    omnara_base_url: str = "https://agent-dashboard-mcp.onrender.com"
    capture_thinking: bool = False
    enable_git_diff: bool = True
    debug: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    auto_launch: bool = True


# CLI wrapper mode
class WrapperMode(str, Enum):
    """Mode for the Gemini wrapper."""
    PROXY = "proxy"  # HTTP/HTTPS proxy mode
    PTY = "pty"      # PTY wrapper for gemini CLI
    SDK = "sdk"      # Direct SDK wrapper


# Error types specific to Gemini
class GeminiError(Exception):
    """Base error for Gemini provider."""
    pass


class GeminiAPIError(GeminiError):
    """API-related errors."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Gemini API Error {status_code}: {message}")


class GeminiProxyError(GeminiError):
    """Proxy-related errors."""
    pass


class GeminiAuthError(GeminiError):
    """Authentication errors."""
    pass


# Helper functions
def extract_text_from_content(content: Content) -> str:
    """Extract text from a content block."""
    text_parts = []
    for part in content.get("parts", []):
        if "text" in part:
            text_parts.append(part["text"])
    return "".join(text_parts)


def extract_text_from_response(response: GeminiResponse) -> str:
    """Extract text from a Gemini response."""
    if not response.get("candidates"):
        return ""
    
    candidate = response["candidates"][0]
    if "content" in candidate:
        return extract_text_from_content(candidate["content"])
    
    return ""


def create_simple_request(prompt: str, **config) -> GeminiRequest:
    """Create a simple Gemini request."""
    request: GeminiRequest = {
        "contents": [
            {
                "parts": [{"text": prompt}],
                "role": "user"
            }
        ]
    }
    
    if config:
        request["generationConfig"] = config
    
    return request


__all__ = [
    # Enums
    "Role",
    "FinishReason",
    "HarmCategory",
    "HarmProbability",
    "WrapperMode",
    
    # Type definitions
    "TextPart",
    "InlineDataPart",
    "Part",
    "Content",
    "GenerationConfig",
    "SafetyRating",
    "SafetySetting",
    "GeminiRequest",
    "Candidate",
    "PromptFeedback",
    "GeminiResponse",
    "StreamChunk",
    "Model",
    
    # Classes
    "GeminiSession",
    "InterceptedMessage",
    "ProxyConfig",
    
    # Errors
    "GeminiError",
    "GeminiAPIError",
    "GeminiProxyError",
    "GeminiAuthError",
    
    # Helper functions
    "extract_text_from_content",
    "extract_text_from_response",
    "create_simple_request",
]