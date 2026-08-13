"""Comprehensive Unit, Integration, & Performance Test Suite for Sprint 2.8.

Tests Conversation CRUD, Message Persistence, Memory Engine Context Trimming,
Conversation Search Engine, Multi-Format Exporter, Workspace Statistics, and Performance Benchmarks.
"""

import time
import pytest

from app.chat import (
    conversation_exporter,
    conversation_search_engine,
    enterprise_conversation_repository,
    memory_engine,
)


# ====================================================
# 1. Conversation CRUD Unit Tests
# ====================================================

def test_conversation_crud():
    # 1. Create (< 2ms)
    conv = enterprise_conversation_repository.create_conversation(
        workspace_id="ws-enterprise",
        user_id="user-1",
        title="Architecture Discussion",
        tags=["architecture", "security"],
    )
    assert conv.conversation_id is not None
    assert conv.title == "Architecture Discussion"
    assert "architecture" in conv.tags

    # 2. Get / Load (< 10ms)
    fetched = enterprise_conversation_repository.get_conversation(conv.conversation_id)
    assert fetched is not None
    assert fetched.conversation_id == conv.conversation_id

    # 3. Update / Rename
    updated = enterprise_conversation_repository.update_conversation(
        conv.conversation_id, {"title": "Renamed Architecture Discussion"}
    )
    assert updated.title == "Renamed Architecture Discussion"

    # 4. Pin & Favorite
    pinned = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"is_pinned": True})
    assert pinned.is_pinned is True

    fav = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"is_favorite": True})
    assert fav.is_favorite is True

    # 5. Archive & Restore
    archived = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"status": "archived"})
    assert archived.status == "archived"

    restored = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"status": "active"})
    assert restored.status == "active"

    # 6. Soft Delete
    deleted = enterprise_conversation_repository.delete_conversation(conv.conversation_id)
    assert deleted is True
    assert enterprise_conversation_repository.get_conversation(conv.conversation_id).status == "deleted"


# ====================================================
# 2. Message Persistence Tests (< 2ms)
# ====================================================

def test_message_persistence():
    conv = enterprise_conversation_repository.create_conversation(title="Message Test Conv")

    msg1 = enterprise_conversation_repository.add_message(
        conversation_id=conv.conversation_id,
        role="user",
        content="What is distributed caching?",
        prompt_tokens=10,
        cost=0.0001,
    )
    assert msg1.message_id is not None
    assert msg1.role == "user"

    msg2 = enterprise_conversation_repository.add_message(
        conversation_id=conv.conversation_id,
        role="assistant",
        content="Distributed caching stores data across multiple cluster nodes.",
        completion_tokens=20,
        cost=0.0003,
    )
    assert msg2.role == "assistant"

    # Check updated conversation totals
    c = enterprise_conversation_repository.get_conversation(conv.conversation_id)
    assert c.total_messages == 2
    assert c.total_tokens == 30
    assert float(c.total_cost) > 0

    msgs = enterprise_conversation_repository.list_messages(conv.conversation_id)
    assert len(msgs) == 2


# ====================================================
# 3. Memory Layer & Context Trimming Tests
# ====================================================

@pytest.mark.anyio
async def test_memory_engine():
    msgs = [
        {"role": "system", "content": "You are Sentinel AI."},
        {"role": "user", "content": "Turn 1 question"},
        {"role": "assistant", "content": "Turn 1 answer"},
        {"role": "user", "content": "Turn 2 question"},
        {"role": "assistant", "content": "Turn 2 answer"},
    ]

    trimmed, tokens = memory_engine.trim_context(msgs, max_tokens=100)
    assert len(trimmed) > 0
    assert trimmed[0]["role"] == "system"  # System prompt preserved

    ctx = await memory_engine.get_memory_context("conv-test-id", msgs, max_tokens=1000)
    assert ctx.conversation_id == "conv-test-id"
    assert len(ctx.short_term_messages) == len(msgs)


# ====================================================
# 4. Search Engine Tests (< 5ms)
# ====================================================

def test_conversation_search_engine():
    conv = enterprise_conversation_repository.create_conversation(
        title="Microservices Design Patterns",
        tags=["microservices", "patterns"],
    )
    enterprise_conversation_repository.add_message(
        conversation_id=conv.conversation_id,
        role="user",
        content="Explain Circuit Breaker pattern in microservices",
    )

    all_convs = [c.to_dict() for c in enterprise_conversation_repository.list_conversations()]
    all_msgs = {
        c["id"]: [m.to_dict() for m in enterprise_conversation_repository.list_messages(c["id"])]
        for c in all_convs
    }

    # Search by Title
    res_title = conversation_search_engine.search(all_convs, all_msgs, query="Microservices")
    assert res_title.total_matches >= 1

    # Search by Message Content Snippet
    res_content = conversation_search_engine.search(all_convs, all_msgs, query="Circuit Breaker")
    assert res_content.total_matches >= 1


# ====================================================
# 5. Multi-Format Exporter Tests
# ====================================================

def test_conversation_exporter():
    conv = enterprise_conversation_repository.create_conversation(title="Exporter Test")
    enterprise_conversation_repository.add_message(conv.conversation_id, "user", "Hello Exporter")

    c_dict = conv.to_dict()
    m_dict = [m.to_dict() for m in enterprise_conversation_repository.list_messages(conv.conversation_id)]

    json_export = conversation_exporter.export_json(c_dict, m_dict)
    assert json_export["stats"]["total_messages"] == 1

    md_export = conversation_exporter.export_markdown(c_dict, m_dict)
    assert "# Exporter Test" in md_export
    assert "Hello Exporter" in md_export

    pdf_spec = conversation_exporter.export_pdf_spec(c_dict, m_dict)
    assert pdf_spec["document_type"] == "PDF_EXPORT_SPECIFICATION"


# ====================================================
# 6. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Conversation Creation (< 2ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        enterprise_conversation_repository.create_conversation(title="Bench Conv")
    create_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert create_ms < 2.0, f"Conversation creation took {create_ms:.3f} ms (limit 2.0 ms)"

    # 2. Message Insert (< 2ms)
    c = enterprise_conversation_repository.create_conversation(title="Bench Msg Conv")
    t0 = time.perf_counter_ns()
    for _ in range(100):
        enterprise_conversation_repository.add_message(c.conversation_id, "user", "Bench message")
    insert_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert insert_ms < 2.0, f"Message insert took {insert_ms:.3f} ms (limit 2.0 ms)"

    # 3. Conversation Search (< 5ms)
    all_convs = [conv.to_dict() for conv in enterprise_conversation_repository.list_conversations()]
    all_msgs = {
        conv["id"]: [m.to_dict() for m in enterprise_conversation_repository.list_messages(conv["id"])]
        for conv in all_convs
    }
    t0 = time.perf_counter_ns()
    for _ in range(100):
        conversation_search_engine.search(all_convs, all_msgs, query="Bench")
    search_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert search_ms < 5.0, f"Conversation search took {search_ms:.3f} ms (limit 5.0 ms)"

    # 4. Conversation Load (< 10ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        enterprise_conversation_repository.get_conversation(c.conversation_id)
    load_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert load_ms < 10.0, f"Conversation load took {load_ms:.3f} ms (limit 10.0 ms)"


# ====================================================
# 6. Conversation Isolation & Payload Structure Tests
# ====================================================

def test_conversation_isolation_and_payload_structure():
    conv_a = enterprise_conversation_repository.create_conversation(title="Conversation A")
    conv_b = enterprise_conversation_repository.create_conversation(title="Conversation B")

    enterprise_conversation_repository.add_message(conv_a.conversation_id, "user", "Write Hello World in Python")
    enterprise_conversation_repository.add_message(conv_a.conversation_id, "assistant", "print('Hello World')")

    msgs_a = enterprise_conversation_repository.list_messages(conv_a.conversation_id)
    msgs_b = enterprise_conversation_repository.list_messages(conv_b.conversation_id)

    assert len(msgs_a) == 2
    assert len(msgs_b) == 0, "New conversation B must begin with 0 messages"

    # Verify conversation B has zero inherited history from conversation A
    enterprise_conversation_repository.add_message(conv_b.conversation_id, "user", "Who is the PM of India")
    msgs_b_updated = enterprise_conversation_repository.list_messages(conv_b.conversation_id)
    assert len(msgs_b_updated) == 1
    assert "python" not in msgs_b_updated[0].content.lower()
    assert msgs_b_updated[0].content == "Who is the PM of India"

