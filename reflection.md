# Lab 5: Static Code Analysis — Reflection

### 1. What is static code analysis, and why is it useful?

Static code analysis examines source code without executing it. It helps identify potential programming errors, security vulnerabilities, and coding-standard violations early in development. This improves code quality, security, and maintainability.

### 2. What differences did you observe between Pylint, Bandit, and Flake8?

Pylint identifies code-quality problems, naming issues, and potential programming mistakes. Bandit focuses on common security weaknesses. Flake8 checks Python style and formatting rules. Using all three tools provides broader coverage than relying on a single tool.

### 3. What issues did you identify and fix?

I fixed the mutable default argument, improved function naming and documentation, corrected file handling, addressed unsafe archive extraction and insecure TLS configuration, replaced the standard XML parser with `defusedxml`, and improved input validation and formatting.

### 4. What are the limitations of static code analysis?

Static-analysis tools cannot identify every logical error or guarantee correct program behaviour. Incorrect business logic may remain even when code passes style and security checks. Static analysis should therefore be combined with functional testing, code review, and security testing.