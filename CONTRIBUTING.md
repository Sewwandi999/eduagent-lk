# Contributing

This repository is an academic student project. Work should be developed in small feature branches and merged through Pull Requests.

## Code quality

- Use Python type hints.
- Validate inter-agent payloads with Pydantic.
- Keep prompts in `src/prompts.py`.
- Do not log API keys or full secret values.
- Add or update tests when changing workflow behaviour.
- Run `pytest -q` before every Pull Request.

## Commit style

Use semantic prefixes:

- `feat:` new capability
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code restructuring without behaviour change
- `test:` tests
- `chore:` maintenance
