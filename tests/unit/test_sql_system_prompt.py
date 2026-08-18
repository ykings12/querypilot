from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parents[2] / "app" / "agents" / "prompts" / "sql_system.txt"


def test_sql_system_prompt_covers_eval_patterns():
    text = PROMPT_PATH.read_text(encoding="utf-8").lower()
    for snippet in (
        "limit",
        "order by",
        "group by",
        "left join",
        "inner join",
        "is not null",
        "round(",
        "validation error",
        "do not add surrogate id",
    ):
        assert snippet in text, f"sql_system.txt should mention {snippet!r}"
