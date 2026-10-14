# Lab 5: Static Code Analysis — Issues and Fixes

**File analysed:** `premium_calculator.py`

**Baseline results**
- Pylint score: 5.73/10
- Bandit: 10 findings (1 high, 5 medium, 4 low)
- Flake8: 19 reported violations

Line numbers below refer to the original, unmodified `premium_calculator.py`.

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---:|---|---|
| Unsafe archive extraction | Security — High (Bandit B202) | 61–65 | `tarfile.extractall()` is used on an archive without validating its members. | Use a safe extraction filter supported by the Python version and validate archive contents and limits. |
| Unverified TLS context | Security — Medium (Bandit B323) | 57–59 | `_create_unverified_context()` disables certificate and hostname verification. | Use `ssl.create_default_context()` and retain certificate verification. |
| Unrestricted URL scheme | Security — Medium (Bandit B310) | 57–59 | `urlopen()` accepts a URL without checking that it uses HTTPS. | Parse and validate the URL scheme and hostname before requesting it; use a timeout. |
| XML parser on untrusted input | Security — Medium (Bandit B314/B405) | 7, 47–48 | `xml.etree.ElementTree` is used to parse externally supplied XML. | Use `defusedxml.ElementTree` and handle malformed XML safely. |
| Hardcoded bind-all address | Security — Medium (Bandit B104) | 12 | `HOST = "0.0.0.0"` may expose a service on all network interfaces if used for listening. | Use a restricted interface such as `127.0.0.1` unless external access is required. |
| Hardcoded authorisation token | Security — Low (Bandit B105) | 13, 73–75 | A token is embedded directly in the source code. | Load the expected token from an environment variable and reject missing configuration. |
| Hardcoded temporary directory | Security — Medium (Bandit B108) | 14 | The log path uses a hardcoded `/tmp` location. | Use an appropriate configurable path or a secure temporary-file API where applicable. |
| Pseudorandom policy number | Security — Low (Bandit B311) | 36–37 | `random.randint()` is used to generate a policy identifier. | Use `secrets` if unpredictability is required and add collision handling for uniqueness. |
| Mutable default argument | Bug / code quality (Pylint W0102) | 17, 27 | `discounts=[]` is shared between calls and the function appends to it. | Use `None` as the default, create a fresh list, and avoid mutating caller-owned data. |
| Broad exception handler | Code quality (Pylint W0702; Flake8 E722; Bandit B112) | 51–54 | A bare `except` hides unexpected errors. | Catch expected exceptions such as `TypeError` and `ValueError`. |
| Missing age birthday check | Logic bug found by code inspection | 30–34 | Age is calculated by subtracting years without checking whether the birthday has occurred. | Compare month and day and subtract one if the birthday is still upcoming. |
| Incorrect smoker argument | Logic bug found by code inspection | 92 | The string `"no"` is truthy in Python and triggers the smoker surcharge. | Pass a Boolean (`False` for a non-smoker) and validate the input type. |
| Negative premium possible | Logic/business-rule bug found by code inspection | 17–28, 93 | Discounts can exceed the premium and produce a negative result. | Validate discounts and apply an explicitly defined minimum-premium rule. |
| File opened without context manager/encoding | Code quality (Pylint R1732/W1514) | 39–45 | The log file is opened without `with` and without an explicit encoding. | Use `with open(..., encoding="utf-8")`. |
| Missing module/function docstrings | Code quality (Pylint C0114/C0116) | 1, functions | The module and several functions lack docstrings. | Add concise module and function docstrings. |
| Non-snake_case function names | Code quality (Pylint C0103) | 17, 30, 36, 39, 47, 57, 61, 67, 73, 79, 83 | Function names do not follow the usual Python naming convention. | Rename functions to `snake_case` and update every call site. |
| Too many function arguments | Code quality (Pylint R0913/R0917) | 17 | `calculatePremium()` has six positional parameters. | Consider a small parameter object or keyword-only arguments if appropriate; avoid unnecessary complexity for this lab. |
| Long lines and spacing violations | Style (Pylint C0301; Flake8 E501/E302/E305) | Various | Several lines exceed the configured limit and blank-line spacing is inconsistent. | Format lines and blank lines to satisfy Flake8 and Pylint. |
| Prefer f-strings and `enumerate()` | Code quality (Pylint C0209/C0200) | 43, 85–87 | Older string formatting and index iteration are used. | Use f-strings and `enumerate()` where appropriate. |
| Unnecessary `else` and Boolean branches | Code quality (Pylint R1703/R1705) | 68–77 | Some functions use unnecessary `else` branches or explicit Boolean returns. | Simplify the control flow without changing behaviour. |

## Notes

1. The tool reports are the baseline. Re-run all three tools after fixing the code and keep the final reports separately.
2. Some findings overlap across tools; for example, the bare `except` is reported by Pylint, Flake8, and Bandit. Do not count overlapping reports as three different code defects.
3. The age, smoker-input, and negative-premium problems were identified by inspecting the program's behaviour; they may not be reported by the static-analysis tools.
4. In the final submission, update this table to describe the fixes actually implemented and verify the final line numbers against the corrected file.
