# Contributing to Akiya Scout

Thank you for your interest in contributing to Akiya Scout! We welcome contributions from everyone, whether it's bug reports, feature requests, documentation improvements, or code changes.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- A GitHub account

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/akiya-scout.git
   cd akiya-scout
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   
   ```bash
   # macOS / Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development tools
   ```

4. **Verify the setup:**
   ```bash
   python -m pytest  # Run tests to confirm everything works
   ```

## Making Changes

### Branch Naming
Create a descriptive branch name for your work:
- `feature/add-search-filters`
- `bugfix/fix-api-timeout`
- `docs/update-readme`

```bash
git checkout -b feature/your-feature-name
```

### Code Style
- Follow [PEP 8](https://pep8.org/) conventions
- Use meaningful variable and function names
- Write docstrings for all functions and classes
- Keep lines under 100 characters where possible

### Testing
Before submitting a pull request:
```bash
# Run tests
pytest

# Check code style
flake8 src/

# Format code (if using black)
black src/
```

## Submitting Changes

### Commit Messages
Write clear, concise commit messages:
- Use the imperative mood ("Add feature" not "Added feature")
- Start with a capital letter
- Keep the first line under 50 characters
- Add details in the body if needed

Examples:
- `Add search filter for property age`
- `Fix IndexError in location validation`
- `Update installation instructions`

### Pull Requests
1. Push your branch to your fork
2. Open a pull request against the main repository
3. Include a clear description of your changes
4. Reference any related issues with `#issue-number`
5. Ensure all tests pass

**PR Title:** Keep it descriptive and concise  
**PR Description:** Include:
- What problem does this solve?
- How does it solve it?
- Any breaking changes?
- Screenshots or examples (if applicable)

## Reporting Issues

### Bugs
Include:
- Python version and OS
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs or error messages

### Feature Requests
Describe:
- The use case you're addressing
- How it would work
- Why it would be useful
- Any alternative approaches you've considered

## Code Review Process

- At least one maintainer review is required
- We'll provide constructive feedback if changes are needed
- Once approved, your PR will be merged
- Thank you for helping improve Akiya Scout!

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers directly.

---

**Happy contributing! 🎉**
