# Contributing to Agentic Infrastructure Portfolio

## Adding a New Example Agent

1. Create a new directory under `examples/`:
   ```
   examples/your-agent-name/
   ├── README.md           # What it does, workflow diagram, tools
   ├── workflow.py         # Runnable demo (stdlib only)
   └── templates/          # Prompt templates, output formats
   ```

2. Requirements for `workflow.py`:
   - Python 3.9+ stdlib only (no pip installs)
   - Dataclasses for core models
   - A main pipeline function (e.g., `process_request()`)
   - Clear console output showing each step
   - Must pass: `python3 workflow.py` with exit code 0

3. Add tests in `tests/test_your_agent.py`:
   - Import the workflow module
   - Test core classification/matching logic
   - Test edge cases
   - Must pass: `python3 tests/test_your_agent.py`

4. Update `README.md`:
   - Add the agent to the example projects list
   - Keep the "Built With" section current

## Code Style

- **Python**: dataclasses for models, type hints, docstrings
- **Markdown**: headers for structure, tables for reference data, ASCII diagrams for workflows
- **Commit messages**: imperative mood, specific (`Add finance ops agent` not `Updates`)
- **No secrets ever**: API keys go in `.env`, never in code

## Running Tests

```bash
cd tests
bash run_all.sh       # Run all tests
python3 test_intake_agent.py   # Run single test
```

## Dashboard Development

```bash
python3 dashboard/app.py --demo   # Demo mode (mock data)
python3 dashboard/app.py          # Live mode (connects to Paperclip)
```

Access at `http://127.0.0.1:9120`

## Questions?

Open an issue or reach out to Alex directly.
