"""Write eval JSONL datasets from validated Chinook question specs."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import asyncpg

from eval.chinook_dataset import (
    BENCHMARK_QUESTIONS,
    DATASET_VERSION,
    golden_questions,
    question_to_json,
)

ROOT = Path(__file__).resolve().parent
GOLDEN_PATH = ROOT / "golden" / "questions.jsonl"
BENCHMARK_PATH = ROOT / "benchmark" / "chinook_questions.jsonl"


def _db_config() -> dict[str, str | int]:
    return {
        "host": os.getenv("EVAL_DB_HOST", "localhost"),
        "port": int(os.getenv("EVAL_DB_PORT", "5433")),
        "database": os.getenv("EVAL_DB_NAME", "chinook"),
        "user": os.getenv("EVAL_DB_USER", "querypilot_readonly"),
        "password": os.getenv("EVAL_DB_PASSWORD", "querypilot_readonly_dev"),
    }


async def _validate_sql(conn: asyncpg.Connection, sql: str) -> None:
    await conn.fetch(sql)


async def validate_questions(questions: list[dict]) -> None:
    conn = await asyncpg.connect(**_db_config())
    try:
        for item in questions:
            await _validate_sql(conn, item["reference_sql"])
    finally:
        await conn.close()


def write_jsonl(path: Path, questions: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, ensure_ascii=True) for item in questions]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def main() -> None:
    benchmark = [question_to_json(item) for item in BENCHMARK_QUESTIONS]
    golden = [question_to_json(item) for item in golden_questions()]

    await validate_questions(benchmark)

    write_jsonl(BENCHMARK_PATH, benchmark)
    write_jsonl(GOLDEN_PATH, golden)
    print(f"Wrote {len(golden)} golden questions -> {GOLDEN_PATH}")
    print(f"Wrote {len(benchmark)} benchmark questions -> {BENCHMARK_PATH}")
    print(f"Dataset version: {DATASET_VERSION}")


if __name__ == "__main__":
    asyncio.run(main())
