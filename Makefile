.PHONY: dev dev-ui test lint docker-up docker-down docker-dev migrate seed-chinook smoke-chat eval-dev eval-dev-quick eval-safety eval-benchmark eval-benchmark-failed build-datasets

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Fastest UI loop: API in Docker, Streamlit on your Mac (auto-reloads on save).
dev-ui:
	API_BASE_URL=http://localhost:8000 .venv/bin/streamlit run ui/streamlit_app.py --server.port 8501

test:
	pytest -q

smoke-chat:
	./scripts/smoke_chat.sh

smoke-phase4:
	.venv/bin/python scripts/smoke_phase4.py

lint:
	ruff check app tests
	ruff format --check app tests

docker-up:
	docker compose up -d --build

# Hot-reload dev stack — build once, then code edits apply without --build
docker-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

docker-api:
	docker compose build api && docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate api

docker-ui:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate ui

docker-down:
	docker compose down

migrate:
	docker compose exec -T metadata-db psql -U querypilot -d querypilot_meta < scripts/init_metadata_db.sql

seed-chinook:
	./scripts/seed_chinook.sh

build-datasets:
	.venv/bin/python -m eval.build_datasets

eval-dev:
	EVAL_HTTP_TIMEOUT=$${EVAL_HTTP_TIMEOUT:-300} \
	EVAL_QUERY_DELAY_SEC=$${EVAL_QUERY_DELAY_SEC:-3} \
	./scripts/run_eval.sh eval/golden/questions.jsonl

eval-safety:
	EVAL_HTTP_TIMEOUT=$${EVAL_HTTP_TIMEOUT:-300} \
	EVAL_QUERY_DELAY_SEC=$${EVAL_QUERY_DELAY_SEC:-2} \
	EVAL_LIMIT=0 \
	./scripts/run_eval.sh eval/golden/questions.jsonl

# ~5–15 min smoke: first 5 golden questions, no 25-case safety suite.
eval-dev-quick:
	EVAL_HTTP_TIMEOUT=$${EVAL_HTTP_TIMEOUT:-240} \
	EVAL_QUERY_DELAY_SEC=$${EVAL_QUERY_DELAY_SEC:-2} \
	EVAL_LIMIT=5 EVAL_SKIP_SAFETY=1 \
	./scripts/run_eval.sh eval/golden/questions.jsonl

eval-benchmark:
	@mkdir -p eval/reports
	./scripts/run_benchmark.sh

eval-benchmark-nohup:
	@chmod +x scripts/run_benchmark_nohup.sh
	@./scripts/run_benchmark_nohup.sh

# Re-run only failed_ids from eval/reports/latest.json (or EVAL_REPORT=...).
eval-benchmark-failed:
	@chmod +x scripts/run_failed_benchmark.sh
	@./scripts/run_failed_benchmark.sh

eval-benchmark-quick:
	@mkdir -p eval/reports
	EVAL_REPORT=eval/reports/$$(date +%Y%m%d_%H%M%S)_report.json \
		./scripts/run_eval.sh eval/benchmark/chinook_questions.jsonl

export-metrics:
	.venv/bin/python scripts/export_traces.py
