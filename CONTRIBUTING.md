# Contributing to HRPO-X

Thank you for your interest in contributing to HRPO-X! This document provides guidelines for contributing to the project.

---

## [*] Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Style](#code-style)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Issue Guidelines](#issue-guidelines)

---

## [#] Code of Conduct

### Our Pledge

We pledge to make participation in HRPO-X a harassment-free experience for everyone.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

---

## [>] Getting Started

### Prerequisites

```bash
# Required
Python 3.10+
Git 2.30+

# Recommended
PyCharm or VSCode
pytest for testing
black for formatting
```

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/hrpo-x.git
cd hrpo-x

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/ -v
```

---

## [>] Development Workflow

### Branch Strategy

```
main                    # Production releases only
├── develop            # Integration branch
├── feature/xyz        # New features
├── fix/xyz           # Bug fixes
└── hotfix/xyz        # Critical production fixes
```

### Creating a Feature Branch

```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/adaptive-temperature

# Make changes and commit
git add .
git commit -m "feat: add adaptive temperature scheduling"

# Push and create PR
git push origin feature/adaptive-temperature
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting changes
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Build/tooling changes

**Example**:
```
feat(ghost): implement bootstrap confidence intervals

- Add _bootstrap_kl_confidence() method
- Increase min_samples to 250
- Improve statistical confidence to 99.9%

Closes #42
```

---

## [T] Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these modifications:

```python
# Line length: 119 characters (not 79)
# Use Black for auto-formatting
# Use type hints for all public functions

def importance_weighted_hrpo_loss(
    policy_logp: torch.Tensor,
    old_policy_logp: torch.Tensor,
    advantages: torch.Tensor,
    step: int,
    config: HRPOConfig
) -> Tuple[Optional[torch.Tensor], Dict]:
    """
    Computes IS-weighted HRPO loss.
    
    Args:
        policy_logp: Current policy log probabilities
        old_policy_logp: Old policy log probabilities
        advantages: Computed advantages
        step: Current training step
        config: HRPO configuration
        
    Returns:
        loss: Computed loss (None if rejected)
        metrics: Diagnostic metrics dict
    """
    # Implementation
```

### Formatting Tools

```bash
# Auto-format with Black
black . --line-length 119

# Sort imports
isort . --profile black

# Check style
flake8 . --max-line-length 119

# Type checking
mypy . --strict
```

### Naming Conventions

```python
# Variables and functions: snake_case
hidden_ratio = 0.15
def compute_advantage():
    pass

# Classes: PascalCase
class AdaptiveRminController:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_SEQUENCE_LENGTH = 2048

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints
- Provide usage examples for complex functions

---

## [B] Testing Requirements

### Test Coverage

- Current: 13 unit tests in tests/test_core.py
- No enforced coverage threshold for this prototype
- Add or update tests when changing core logic

### Writing Tests

```python
# tests/test_core_config.py
from hrpox import HRPOConfig

class TestHRPOConfig:
    """Basic sanity checks for the prototype config"""

    def test_defaults(self):
        config = HRPOConfig()
        assert config.beta > 0
        assert 0.0 < config.target_hidden_ratio < 1.0
```


### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_core.py -v

# With coverage
pytest tests/ --cov=hrpox --cov-report=html

# Skip slow tests
pytest tests/ -v -m "not slow"

# Run only unit tests
pytest tests/unit/ -v
```

---

## [>] Pull Request Process

### Before Submitting

1. **Run Tests**: `pytest tests/ -v`
2. **Format Code**: `black . && isort .`
3. **Update Docs**: Modify relevant `.md` files
4. **Update CHANGELOG**: Add entry under `[Unreleased]`
5. **Verify Build**: `python setup.py build`

### PR Template

```markdown
## [*] Description

Brief description of changes and motivation.

## [!] Type of Change

- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## [B] Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Coverage maintained/improved

## [L] Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new warnings generated

## [#] Related Issues

Closes #123
Relates to #456
```

### Review Process

1. **Automated Checks**: CI runs tests, linting, coverage
2. **Code Review**: At least 1 approval required
3. **Documentation Review**: Docs team reviews if applicable
4. **Final Approval**: Maintainer approval required

### Merge Criteria

- ✓ All CI checks pass
- ✓ Code review approved
- ✓ Coverage ≥ 80%
- ✓ Documentation updated
- ✓ No merge conflicts

---

## [L] Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**[!] Bug Description**
Clear description of the bug

**[>] Steps to Reproduce**
1. Step 1
2. Step 2
3. See error

**[o] Expected Behavior**
What should happen

**[!] Actual Behavior**
What actually happens

**[T] Environment**
- OS: Windows 11
- Python: 3.10.5
- HRPO-X: 2.2.0

**[L] Additional Context**
Screenshots, logs, etc.
```

### Feature Requests

Use the feature request template:

```markdown
**[*] Feature Description**
Clear description of proposed feature

**[o] Use Case**
Why is this needed?

**[!] Proposed Solution**
How should it work?

**[=] Alternatives Considered**
What other approaches were considered?

**[L] Additional Context**
Mockups, references, etc.
```

---

## [W] Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in paper acknowledgments (major contributions)

---

## [+] Questions?

- **Discord**: [Join our server](https://discord.gg/hrpo-x)
- **Email**: contributors@flamehaven.io
- **Discussions**: [GitHub Discussions](https://github.com/your-org/hrpo-x/discussions)

---

**Thank you for contributing to HRPO-X!**

**Reference**: HRPO-inspired research notes (no verified paper implementation)
**Maintained By**: Flamehaven Labs / CLI C01
