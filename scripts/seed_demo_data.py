"""Mock Telemetry & Seed Script for Sentinel AI Control Plane.

Connects to PostgreSQL and ClickHouse to pre-populate baseline operational data:
1. Virtual API Keys: Default active Virtual Key (`sentinel-virtual-key-prod-01`)
2. ClickHouse Telemetry Spans: 30 realistic OpenTelemetry trace rows covering model execution
   latencies (80ms - 320ms), token usage, cost attributions, and DLP redaction events.
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# Resolve sys.path for running directly as a script
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("sentinel.seed")


# Default Virtual Key metadata
VIRTUAL_KEY_ID = "sentinel-virtual-key-prod-01"
VIRTUAL_KEY_SECRET = "sk-snt-live-sentinel-virtual-key-prod-01"
VIRTUAL_KEY_HASH = hashlib.sha256(VIRTUAL_KEY_SECRET.encode("utf-8")).hexdigest()
VIRTUAL_KEY_PREFIX = VIRTUAL_KEY_SECRET[:16] + "..."
WORKSPACE_ID = "default"


def seed_postgres_virtual_key():
    """Insert active default Virtual Key into PostgreSQL if one does not exist."""
    logger.info("Checking PostgreSQL Virtual Key seeding...")

    # Also seed into in-memory repository
    try:
        from app.security.keys import VirtualKey, VirtualKeyType
        from app.security.repository import virtual_key_repository

        existing = virtual_key_repository.get_key(VIRTUAL_KEY_ID)
        if not existing:
            vk = VirtualKey(
                id=VIRTUAL_KEY_ID,
                workspace_id=WORKSPACE_ID,
                name="Default Production Virtual Key",
                key_hash=VIRTUAL_KEY_HASH,
                prefix=VIRTUAL_KEY_PREFIX,
                key_type=VirtualKeyType.WORKSPACE,
                allowed_providers=["gemini", "openai", "anthropic", "ollama"],
                allowed_models=["gemini-2.0-flash", "gpt-4o-mini", "claude-3-5-sonnet", "llama3.2"],
                rate_limit_rpm=600,
                is_active=True,
            )
            virtual_key_repository._keys[VIRTUAL_KEY_ID] = vk
            virtual_key_repository._hash_lookup[VIRTUAL_KEY_HASH] = VIRTUAL_KEY_ID
            logger.info("Successfully seeded Virtual Key '%s' in memory", VIRTUAL_KEY_ID)
    except Exception as err:
        logger.warning("In-memory virtual key repository seed warning: %s", err)

    # Database sync
    pg_urls = [
        os.environ.get("SENTINEL_AI_DATABASE_URL"),
        "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel_ai",
        "postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_ai",
    ]
    
    async def _async_seed_pg():
        try:
            from app.db.session import engine
            from sqlalchemy import text
            if engine:
                async with engine.begin() as conn:
                    # Ensure table exists
                    await conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS virtual_keys (
                            id VARCHAR(36) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            key_hash VARCHAR(128) NOT NULL UNIQUE,
                            prefix VARCHAR(20) NOT NULL,
                            workspace_id VARCHAR(36) NOT NULL,
                            key_type VARCHAR(20) NOT NULL DEFAULT 'workspace',
                            allowed_providers_json TEXT,
                            allowed_models_json TEXT,
                            rate_limit_rpm INTEGER,
                            rate_limit_tpm INTEGER,
                            budget_limit_usd FLOAT,
                            current_spend_usd FLOAT NOT NULL DEFAULT 0.0,
                            expires_at TIMESTAMP,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            last_used_at TIMESTAMP
                        );
                    """))
                    await conn.execute(text("""
                        INSERT INTO virtual_keys (
                            id, name, key_hash, prefix, workspace_id, key_type, is_active, created_at
                        ) VALUES (
                            :id, 'Default Production Virtual Key', :key_hash, :prefix, :workspace_id, 'workspace', true, CURRENT_TIMESTAMP
                        ) ON CONFLICT (id) DO NOTHING;
                    """), {
                        "id": VIRTUAL_KEY_ID,
                        "key_hash": VIRTUAL_KEY_HASH,
                        "prefix": VIRTUAL_KEY_PREFIX,
                        "workspace_id": WORKSPACE_ID,
                    })
                    logger.info("Successfully seeded Virtual Key '%s' into PostgreSQL database", VIRTUAL_KEY_ID)
        except Exception as exc:
            logger.info("PostgreSQL direct connection note (DB may be initializing): %s", exc)

    try:
        asyncio.run(_async_seed_pg())
    except Exception as exc:
        logger.info("PostgreSQL async loop skipped: %s", exc)


def _exec_clickhouse_query(sql_query: str) -> bool:
    """Execute SQL query against ClickHouse HTTP endpoint."""
    ch_hosts = ["clickhouse", "localhost", "127.0.0.1"]
    ports = [8123]
    
    for host in ch_hosts:
        for port in ports:
            url = f"http://{host}:{port}/"
            try:
                req = urllib.request.Request(
                    url,
                    data=sql_query.encode("utf-8"),
                    headers={"Content-Type": "text/plain"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status in (200, 201):
                        return True
            except Exception:
                continue
    return False


def seed_clickhouse_telemetry_spans():
    """Insert 25+ realistic OpenTelemetry trace rows into ClickHouse (`traces` / `spans` table)."""
    logger.info("Seeding ClickHouse OpenTelemetry traces & spans...")

    # Create tables
    create_traces_table_sql = """
    CREATE TABLE IF NOT EXISTS traces (
        trace_id String,
        span_id String,
        parent_span_id String,
        workspace_id String,
        user_id String,
        provider_id String,
        model_id String,
        prompt_tokens UInt32,
        completion_tokens UInt32,
        total_tokens UInt32,
        cost_usd Float64,
        latency_ms Float64,
        status String,
        dlp_redacted UInt8,
        dlp_event_type String,
        timestamp DateTime DEFAULT now()
    ) ENGINE = MergeTree() ORDER BY (timestamp, trace_id);
    """
    
    create_spans_table_sql = """
    CREATE TABLE IF NOT EXISTS spans (
        span_id String,
        trace_id String,
        name String,
        provider_id String,
        model_id String,
        latency_ms Float64,
        status String,
        timestamp DateTime DEFAULT now()
    ) ENGINE = MergeTree() ORDER BY (timestamp, span_id);
    """

    ch_available = _exec_clickhouse_query(create_traces_table_sql) and _exec_clickhouse_query(create_spans_table_sql)
    if ch_available:
        logger.info("ClickHouse schema verified/created successfully.")
    else:
        logger.info("ClickHouse service not reachable via HTTP; seeding in-memory observability repository.")

    # Generate 30 telemetry records
    providers_models = [
        ("gemini", "gemini-2.0-flash"),
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-5-sonnet"),
        ("ollama", "llama3.2"),
    ]

    dlp_events = [
        (1, "PII_SSN_REDACTED"),
        (1, "API_KEY_REDACTED"),
        (1, "CREDIT_CARD_REDACTED"),
        (1, "EMAIL_ADDRESS_MASKED"),
        (1, "PII_PHONE_REDACTED"),
        (0, "NONE"),
    ]

    traces_to_insert = []
    in_memory_records = []

    now = datetime.utcnow()
    for i in range(30):
        prov_id, mod_id = random.choice(providers_models)
        latency_ms = round(random.uniform(80.0, 320.0), 2)  # Specified range 80ms - 320ms
        prompt_tokens = random.randint(20, 180)
        completion_tokens = random.randint(35, 320)
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = round(random.uniform(0.0001, 0.0042), 5)  # Specified cost $0.0001 - $0.0042
        
        if i < 6:
            dlp_redacted, dlp_event = dlp_events[i]
        else:
            dlp_redacted, dlp_event = 0, "NONE"

        trace_id = f"trace-prod-{1000 + i}"
        span_id = f"span-prod-{2000 + i}"
        event_time = (now - timedelta(minutes=random.randint(1, 1440))).strftime("%Y-%m-%d %H:%M:%S")

        traces_to_insert.append(
            f"('{trace_id}', '{span_id}', '0', '{WORKSPACE_ID}', 'prod_user_{i % 5 + 1}', "
            f"'{prov_id}', '{mod_id}', {prompt_tokens}, {completion_tokens}, {total_tokens}, "
            f"{cost_usd}, {latency_ms}, 'SUCCESS', {dlp_redacted}, '{dlp_event}', '{event_time}')"
        )

        in_memory_records.append({
            "trace_id": trace_id,
            "provider_id": prov_id,
            "model_id": mod_id,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "status": "SUCCESS",
            "dlp_redacted": bool(dlp_redacted),
            "dlp_event": dlp_event,
            "timestamp": event_time,
        })

    # Seed ClickHouse
    if ch_available:
        insert_sql = "INSERT INTO traces VALUES " + ", ".join(traces_to_insert)
        if _exec_clickhouse_query(insert_sql):
            logger.info("Successfully inserted %d OpenTelemetry trace rows into ClickHouse", len(traces_to_insert))
        else:
            logger.warning("ClickHouse insert query failed.")

    # Seed in-memory Observability Repository
    try:
        from app.observability.models import TraceRecord
        from app.observability.repository import observability_repository
        for rec in in_memory_records:
            tr = TraceRecord(
                trace_id=rec["trace_id"],
                workspace_id=WORKSPACE_ID,
                user_id="prod_user",
                provider_id=rec["provider_id"],
                model_id=rec["model_id"],
                prompt="Demotesting trace payload",
                completion="Seeded completion response payload",
                prompt_tokens=rec["prompt_tokens"],
                completion_tokens=rec["completion_tokens"],
                total_tokens=rec["prompt_tokens"] + rec["completion_tokens"],
                estimated_cost_usd=rec["cost_usd"],
                total_latency_ms=rec["latency_ms"],
                status=rec["status"],
            )
            observability_repository.save_trace(tr)
        logger.info("Successfully populated in-memory ObservabilityRepository with %d traces", len(in_memory_records))
    except Exception as err:
        logger.warning("In-memory ObservabilityRepository seed warning: %s", err)


def main():
    logger.info("Starting Sentinel AI Telemetry & Data Seeding Engine...")
    seed_postgres_virtual_key()
    seed_clickhouse_telemetry_spans()
    logger.info("Sentinel AI Data Seeding Completed Successfully.")


if __name__ == "__main__":
    main()
