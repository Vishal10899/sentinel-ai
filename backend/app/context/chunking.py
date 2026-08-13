import json
import re
from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass
class Chunk:
    """Document text chunk prepared for vector indexing and LLM context window ingestion."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    token_count: int
    page_number: int = 1
    metadata_json: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ChunkingEngine:
    """Enterprise text chunking engine supporting fixed, sentence, and paragraph strategies."""

    def __init__(self, default_chunk_size: int = 512, default_overlap: int = 50) -> None:
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap

    def chunk_text(
        self,
        document_id: str,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        strategy: str = "sentence",
        page_number: int = 1,
    ) -> list[Chunk]:
        """Split raw text into structured chunks preserving metadata offsets."""
        if not text or not text.strip():
            return []

        c_size = chunk_size or self.default_chunk_size
        c_overlap = chunk_overlap or self.default_overlap

        if strategy == "paragraph":
            units = text.split("\n\n")
        elif strategy == "sentence":
            units = re.split(r"(?<=[.!?])\s+", text)
        else:
            units = [text]

        chunks: list[Chunk] = []
        current_unit_buffer: list[str] = []
        current_len = 0
        current_start = 0
        chunk_idx = 0

        char_offset = 0

        for unit in units:
            unit_str = unit.strip()
            if not unit_str:
                continue

            unit_len = len(unit_str)

            if current_len + unit_len > c_size and current_unit_buffer:
                chunk_content = " ".join(current_unit_buffer)
                end_char = current_start + len(chunk_content)
                token_count = max(len(chunk_content) // 4, 1)

                chunks.append(
                    Chunk(
                        chunk_id=str(uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_idx,
                        text=chunk_content,
                        start_char=current_start,
                        end_char=end_char,
                        token_count=token_count,
                        page_number=page_number,
                    )
                )
                chunk_idx += 1

                # Retain overlap from end of buffer
                overlap_text = chunk_content[-c_overlap:] if len(chunk_content) > c_overlap else ""
                current_unit_buffer = [overlap_text, unit_str] if overlap_text else [unit_str]
                current_len = len(" ".join(current_unit_buffer))
                current_start = max(end_char - len(overlap_text), 0)
            else:
                current_unit_buffer.append(unit_str)
                current_len += unit_len + 1

        if current_unit_buffer:
            chunk_content = " ".join(current_unit_buffer).strip()
            if chunk_content:
                token_count = max(len(chunk_content) // 4, 1)
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_idx,
                        text=chunk_content,
                        start_char=current_start,
                        end_char=current_start + len(chunk_content),
                        token_count=token_count,
                        page_number=page_number,
                    )
                )

        return chunks


chunking_engine = ChunkingEngine()
