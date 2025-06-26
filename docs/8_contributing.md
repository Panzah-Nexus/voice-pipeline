# 8. Contributing

We welcome contributions to the Voice Pipeline project! This guide outlines the standards and procedures to follow to ensure a smooth and collaborative development process.

## Code Style

*   **Python:** We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide, with code formatted using **Black**.
*   **Markdown:** Documentation is written in **GitHub-Flavored Markdown**.
*   **Imports:** Imports should be sorted using **isort**.
*   **Type Hinting:** All new functions and methods should include type hints.

## Pre-Commit Hooks

To automatically enforce code style and catch common issues before they are committed, we use a set of pre-commit hooks.

### Setup

Install the pre-commit hooks into your local repository clone:

```bash
# Install the pre-commit package if you haven't already
pip install pre-commit

# Set up the git hook scripts
pre-commit install
```

### Usage

Once installed, the hooks will run automatically on every `git commit` command. They will check for issues with formatting, linting, and more. If a hook modifies a file (e.g., Black reformatting code), the commit will be aborted. Simply review the changes and `git add` the files again to proceed with the commit.

You can also run the hooks manually on all files at any time:

```bash
pre-commit run --all-files
```

## Running Unit Tests

[This section is a placeholder. Please add details on the project's testing framework and how to run the test suite.]

Before submitting a pull request, please ensure that all existing unit tests pass and that you have added new tests to cover your changes.

```bash
# Example command for running tests (please update)
pytest
```

## Submitting Changes

1.  **Fork the repository** and create a new branch for your feature or bug fix.
2.  **Make your changes**, adhering to the code style guidelines.
3.  **Add unit tests** for your changes.
4.  **Ensure all tests pass** and that the pre-commit hooks run without errors.
5.  **Submit a pull request** with a clear description of the changes you have made. 