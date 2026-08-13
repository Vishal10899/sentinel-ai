"""Prompt Analyzer module for extracting structured metadata from incoming requests."""

import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PromptAnalysisResult:
    """Structured prompt metadata extracted during routing pipeline evaluation."""

    prompt_length: int
    estimated_tokens: int
    detected_language: str | None
    output_format: str
    reasoning_depth: str
    context_size: int
    has_code: bool
    has_files: bool
    has_images: bool
    has_math: bool
    keywords_found: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "prompt_length": self.prompt_length,
            "estimated_tokens": self.estimated_tokens,
            "detected_language": self.detected_language,
            "output_format": self.output_format,
            "reasoning_depth": self.reasoning_depth,
            "context_size": self.context_size,
            "has_code": self.has_code,
            "has_files": self.has_files,
            "has_images": self.has_images,
            "has_math": self.has_math,
            "keywords_found": list(self.keywords_found),
        }


class PromptAnalyzer:
    """Extract metadata, programming languages, reasoning depth, and content flags from prompts."""

    _LANGUAGE_PATTERNS = {
        "python": r"\b(def\s+\w+|import\s+\w+|from\s+\w+\s+import|async\s+def|print\(|self\.|sys\.|os\.)\b|```python",
        "javascript": r"\b(const\s+\w+|let\s+\w+|var\s+\w+|function\s+\w+|console\.log|=>|export\s+default|import\s+.*from)\b|```javascript|```js",
        "typescript": r"\b(interface\s+\w+|type\s+\w+\s*=|enum\s+\w+|:\s*string|:\s*number|:\s*boolean|implements\s+\w+)\b|```typescript|```ts",
        "sql": r"\b(SELECT\s+.*FROM|INSERT\s+INTO|UPDATE\s+.*SET|DELETE\s+FROM|CREATE\s+TABLE|ALTER\s+TABLE|JOIN\s+\w+\s+ON|GROUP\s+BY|ORDER\s+BY)\b|```sql",
        "java": r"\b(public\s+class|private\s+void|System\.out\.println|package\s+[\w\.]+;|@Override)\b|```java",
        "c++": r"\b(#include\s+<\w+>|std::cout|std::vector|int\s+main\(\)|template\s*<typename)\b|```cpp|```c\+\+",
        "rust": r"\b(fn\s+\w+|let\s+mut\s+|impl\s+\w+|pub\s+fn|match\s+\w+\s*\{|println!)\b|```rust",
        "go": r"\b(package\s+main|func\s+\w+|import\s*\(\s*\"|fmt\.Println|go\s+func)\b|```go",
        "html": r"</?(html|div|span|p|a|table|tr|td|body|head|script)\b|<!DOCTYPE html>",
        "css": r"\b(color:\s*|background-color:|margin:|padding:|display:\s*flex|font-family:)\b",
        "bash": r"\b(curl\s+|wget\s+|chmod\s+|chown\s+|grep\s+|awk\s+|sed\s+|docker\s+|kubectl\s+)\b|```bash|```sh",
    }

    _MATH_PATTERNS = [
        r"\b(calculate|solve|equation|integral|derivative|matrix|algebra|geometry|theorem|proof|logarithm|exponent)\b",
        r"[\d\w\)]\s*[\+\-\*/\^=]\s*[\d\w\(]",
        r"\\\(.*\\\)|\\\[.*\\\]|\$\$.*\$\$",
    ]

    _REASONING_PATTERNS = [
        r"\b(step[- ]by[- ]step|explain|why|analyze|reason|deduce|logic|compare|contrast|tradeoff|evaluate|proof|architect)\b"
    ]

    def analyze(
        self,
        prompt: str,
        system_prompt: str = "",
        has_attachments: bool = False,
        has_images: bool = False,
    ) -> PromptAnalysisResult:
        """Analyze prompt and extract structured routing metadata."""
        text = prompt.strip()
        full_text = f"{system_prompt}\n{text}".strip()

        length = len(text)
        estimated_tokens = max(len(full_text) // 4, 1)

        # Programming language detection
        detected_lang = None
        for lang, pattern in self._LANGUAGE_PATTERNS.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                detected_lang = lang
                break

        # Presence of code blocks or syntax
        has_code = (
            detected_lang is not None
            or "```" in full_text
            or bool(re.search(r"\b(code|function|class|method|variable|bug|error|traceback)\b", full_text, re.IGNORECASE))
        )

        # Presence of math
        has_math = any(bool(re.search(p, full_text, re.IGNORECASE)) for p in self._MATH_PATTERNS)

        # Reasoning depth analysis
        reasoning_matches = sum(len(re.findall(p, full_text, re.IGNORECASE)) for p in self._REASONING_PATTERNS)
        if reasoning_matches >= 3 or len(text) > 3000:
            reasoning_depth = "high"
        elif reasoning_matches >= 1 or len(text) > 800:
            reasoning_depth = "medium"
        else:
            reasoning_depth = "low"

        # Requested output format
        if "json" in full_text.lower() or "schema" in full_text.lower():
            output_format = "json"
        elif has_code or "code" in full_text.lower():
            output_format = "code"
        elif "markdown" in full_text.lower() or "table" in full_text.lower():
            output_format = "markdown"
        elif "summary" in full_text.lower() or "bullet" in full_text.lower():
            output_format = "structured"
        else:
            output_format = "plain_text"

        keywords_found = []
        for kw in ["api", "db", "sql", "architecture", "security", "docker", "test", "fix", "refactor"]:
            if re.search(rf"\b{kw}\b", full_text, re.IGNORECASE):
                keywords_found.append(kw)

        return PromptAnalysisResult(
            prompt_length=length,
            estimated_tokens=estimated_tokens,
            detected_language=detected_lang,
            output_format=output_format,
            reasoning_depth=reasoning_depth,
            context_size=estimated_tokens + (1000 if has_attachments else 0),
            has_code=has_code,
            has_files=has_attachments,
            has_images=has_images,
            has_math=has_math,
            keywords_found=tuple(keywords_found),
        )


prompt_analyzer = PromptAnalyzer()
