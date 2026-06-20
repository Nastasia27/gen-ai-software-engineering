# Homework 6 — Task List (Capstone: AI-Powered Multi-Agent Banking Pipeline)

> Стек: **Python** (pytest + pytest-cov, FastMCP, `decimal.Decimal`, `uv`).
> Автор: **Anastasia Kopiika**.
> 📸 = крок зі скриншотом. На цих кроках зупиняємось і робимо знімок у `docs/screenshots/`.

---

## Етап 0 — Каркас проєкту
- [x] Створити структуру папок: `agents/`, `mcp/`, `tests/`, `.claude/commands/`, `docs/screenshots/`
- [x] Створити `shared/{input,processing,output,results}/` з `.gitkeep` у кожній
- [x] `requirements.txt` (fastmcp, pytest, pytest-cov)
- [x] `.gitignore` (`__pycache__/`, `.venv/`, `shared/*/` крім `.gitkeep`)
- [x] Перевірити, що `sample-transactions.json` на місці

---

## Етап 1 — Агент 1: Специфікація
- [x] `specification.md` — 5 секцій (High-Level, Mid-Level 4–5 пунктів, Implementation Notes, Context, Low-Level Tasks по агенту)
- [x] `agents.md` — розширити банківськими правилами (Decimal, ISO 4217, no-PII-logging, audit-trail)
- [x] Skill `.claude/commands/write-spec.md` (генерує spec за шаблоном)

---

## Етап 2 — Агент 2: Конвеєр (3+ агенти) + context7
- [x] `agents/transaction_validator.py` — поля, додатня сума, ISO 4217 (валить TXN006 `XYZ`)
- [x] `agents/fraud_detector.py` — risk score (high-value, нічний час, cross-border)
- [x] `agents/settlement_processor.py` — нетто-сума з `ROUND_HALF_UP` (3-й агент)
- [x] `integrator.py` — створює `shared/`, читає sample, ганяє агентів по черзі через JSON, збирає `results/`
- [x] Використати **context7** під час кодингу (decimal, FastMCP)
- [x] `research-notes.md` — ≥2 запити context7 (search + library ID + застосований інсайт)
- [x] Прогнати: усі 8 транзакцій з'являються в `shared/results/` (6 settled, 1 flagged, 2 rejected)
- [x] 📸 **pipeline-run.png** — повний вивід терміналу `python integrator.py`
- [ ] 📸 **mcp-interaction.png (частина 1)** — результат запиту до **context7**

---

## Етап 3 — Агент 3: Skills + Coverage-gate Hook
- [ ] `.claude/commands/run-pipeline.md`
- [ ] `.claude/commands/validate-transactions.md`
- [ ] Coverage-gate hook у `.claude/settings.json` — `pytest --cov`, блокує push при <80%
- [ ] Дубль-скрипт `.git/hooks/pre-push` (щоб гейт спрацьовував і поза Claude)
- [ ] 📸 **skill-run-pipeline.png** — виконання skill `/run-pipeline`
- [ ] 📸 **hook-trigger.png** — як hook блокує push при coverage < 80%

---

## Етап 4 — MCP (context7 + кастомний сервер)
- [ ] `mcp/server.py` (FastMCP): tool `get_transaction_status`, tool `list_pipeline_results`, resource `pipeline://summary`
- [ ] `mcp.json` — context7 + pipeline-status
- [ ] Перевірити, що обидва сервери відповідають
- [ ] 📸 **mcp-interaction.png (частина 2)** — виклик кастомного MCP-tool (напр. `get_transaction_status`)

---

## Етап 5 — Агент 4: Тести + Документація
- [ ] `tests/` — unit на кожен агент + 1 інтеграційний тест конвеєра
- [ ] Ізоляція тестів від реального `shared/` (через `tmp_path`)
- [ ] Coverage ≥ 80% (гейт), ціль ≥ 90%
- [ ] `README.md` — **ім'я Anastasia Kopiika**, опис системи, агенти, ASCII-діаграма, tech-stack table
- [ ] `HOWTORUN.md` — покрокова інструкція setup → demo
- [ ] 📸 **test-coverage.png** — звіт покриття ≥ 80% (бажано ≥ 90%)

---

## Етап 6 — Сабміт: скриншоти + PR
- [ ] Усі **5 обов'язкових** скриншотів у `docs/screenshots/`:
  - [ ] `pipeline-run.png`
  - [ ] `test-coverage.png`
  - [ ] `skill-run-pipeline.png`
  - [ ] `hook-trigger.png`
  - [ ] `mcp-interaction.png` (context7 + кастомний MCP в одному кадрі/серії)
- [ ] `PR_DESCRIPTION.md` — ті ж скриншоти вбудовані/залінковані
- [ ] Фінальна перевірка по **Success Criteria** з `TASKS.md`

---

## 📸 Зведена таблиця скриншотів (обов'язкові 5)
| Файл | Що знімати | Етап |
|---|---|---|
| `pipeline-run.png` | повний вивід `python integrator.py` | 2 |
| `mcp-interaction.png` | context7 запит **+** виклик кастомного MCP-tool | 2 + 4 |
| `skill-run-pipeline.png` | skill `/run-pipeline` у дії | 3 |
| `hook-trigger.png` | coverage-gate hook блокує push (<80%) | 3 |
| `test-coverage.png` | звіт покриття ≥ 80% | 5 |
