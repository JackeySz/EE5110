# Contributing

## Workflow

1. Read `AGENTS.md`, the architecture and interface documents, and your task file.
2. Create the branch listed in `README.md`.
3. Modify only the files in your assigned scope unless another owner agrees.
4. Add or update tests for observable behavior.
5. Run `pytest`, `ruff check .`, and `mypy src`.
6. Open a pull request using the repository template.
7. Obtain at least one human review before merging.

## Interface changes

Public API changes require agreement from affected module owners. Record the decision in `docs/DECISIONS.md`, update `docs/INTERFACES.md`, then update implementation and tests in the same pull request.

## AI-generated changes

AI output is a draft. Review every changed line, verify equations independently, run the required tests, and record material AI use for the course report.
