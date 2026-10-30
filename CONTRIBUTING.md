# Contributing to VerseWatcher

Thanks for your interest in contributing to VerseWatcher. We welcome bug reports, fixes, feature ideas, and improvements.

This project is licensed under the MIT License. By contributing code, documentation, or other materials to this repository, you agree that your contributions will be licensed under the same MIT terms as the project.

## Code of Conduct

Please also review the repository's Code of Conduct before participating.

## How to Contribute

### 1. Report bugs or suggest improvements

- Check existing issues before opening a new one.
- Use a clear title and include as much detail as possible.
- Include:
  - steps to reproduce
  - expected behavior
  - actual behavior
  - relevant logs or screenshots
  - your environment (Windows version, Python version, app version, etc.)

### 2. Fork and branch

1. Fork the repository.
2. Create a branch for your work.
3. Keep your changes focused and avoid unrelated edits.

Example:

```bash
git checkout -b fix/kill-event-parser
```

### 3. Make your changes

- Follow the existing project structure and coding style.
- Prefer small, well-documented changes.
- Update documentation when behavior or setup changes.
- Keep backups or generated files out of the final patch unless they are necessary.

### 4. Validate your work

Before submitting a pull request:

- Run any relevant checks or tests locally.
- Verify the project still starts correctly.
- Confirm the change behaves as expected in the target environment.

### 5. Submit a pull request

Open a pull request with:

- a clear title
- a concise summary of the change
- the reason for the change
- any testing or verification performed
- screenshots or examples if relevant

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/PINKgeekPDX/VerseWatcher.git
cd VerseWatcher
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the project:

```bash
python src/main.py
```

## Coding Standards

- Use clear, readable Python code.
- Keep functions and modules focused.
- Prefer explicit, maintainable logic over clever shortcuts.
- Follow existing naming conventions used in the repository.
- If you add or change behavior, document it clearly.

## Licensing

By contributing to VerseWatcher, you agree that:

- your contribution is your original work, or you have the right to contribute it;
- your contribution will be distributed under the project's MIT License;
- the repository maintainers may use, modify, and redistribute your contribution under the same license.

The full license text is available in the repository's `LICENSE` file.

## Contributor Notes

We appreciate thoughtful, well-scoped contributions. If you are unsure whether a change fits the project, open an issue first and discuss it before submitting a large PR.

Thank you for helping improve VerseWatcher.
