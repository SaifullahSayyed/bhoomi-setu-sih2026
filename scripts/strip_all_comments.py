"""
strip_all_comments.py — Script to remove comments from Python, JS, JSX, Solidity, and CSS files
while preserving strings, regexes, and code functionality.
"""

import re
import tokenize
import io
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

def strip_python_comments(content: str) -> str:
    """Removes # comments and standalone string docstrings from Python code."""
    try:
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        result = []
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                continue
            result.append(tok)
        return tokenize.untokenize(result)
    except Exception as e:
        print(f"Tokenize failed, using fallback regex: {e}")
        # Fallback line-by-line for simple # comments
        lines = []
        for line in content.splitlines():
            if line.strip().startswith("#"):
                continue
            lines.append(line)
        return "\n".join(lines)


def strip_c_style_comments(content: str) -> str:
    """
    Strips // and /* */ comments from JS, JSX, Solidity, and CSS
    without affecting string literals ("...", '...', `...`) or URLs.
    """
    pattern = r"""
        ( "(?:\\.|[^"\\])*" ) |        # Double-quoted string
        ( '(?:\\.|[^'\\])*' ) |        # Single-quoted string
        ( `(?:\\.|[^`\\])*` ) |        # Template literal
        ( /\*(?:[^*]|\*+[^/*])*\*+/ ) | # Block comment
        ( //.* )                        # Line comment
    """
    def replacer(match):
        if match.group(1): return match.group(1)
        if match.group(2): return match.group(2)
        if match.group(3): return match.group(3)
        return "" # Strip block or line comment

    cleaned = re.sub(pattern, replacer, content, flags=re.VERBOSE)
    
    # Also strip JSX-style {/* ... */} comments
    cleaned = re.sub(r'\{\s*/\*.*?\*/\s*\}', '', cleaned, flags=re.DOTALL)
    
    # Clean up empty consecutive lines
    cleaned_lines = [line for line in cleaned.splitlines() if line.strip() != ""]
    return "\n".join(cleaned_lines) + "\n"


def process_all_files():
    py_files = list(REPO_ROOT.glob("backend/**/*.py")) + list(REPO_ROOT.glob("scripts/**/*.py")) + list(REPO_ROOT.glob("tests/**/*.py"))
    js_files = (
        list(REPO_ROOT.glob("contracts/**/*.sol")) +
        list(REPO_ROOT.glob("contracts/**/*.js")) +
        list(REPO_ROOT.glob("frontend/src/**/*.js")) +
        list(REPO_ROOT.glob("frontend/src/**/*.jsx")) +
        list(REPO_ROOT.glob("frontend/test/**/*.js"))
    )

    # Exclude node_modules, dist, .git, and strip_all_comments.py itself
    py_files = [f for f in py_files if "node_modules" not in str(f) and f.name != "strip_all_comments.py"]
    js_files = [f for f in js_files if "node_modules" not in str(f) and "dist" not in str(f) and "artifacts" not in str(f) and "cache" not in str(f)]

    print(f"Processing {len(py_files)} Python files...")
    for f in py_files:
        print(f"  Stripping comments from: {f.relative_to(REPO_ROOT)}")
        original = f.read_text(encoding="utf-8")
        cleaned = strip_python_comments(original)
        f.write_text(cleaned, encoding="utf-8")

    print(f"\nProcessing {len(js_files)} JS / JSX / Solidity files...")
    for f in js_files:
        print(f"  Stripping comments from: {f.relative_to(REPO_ROOT)}")
        original = f.read_text(encoding="utf-8")
        cleaned = strip_c_style_comments(original)
        f.write_text(cleaned, encoding="utf-8")

    print("\nAll comments removed successfully.")

if __name__ == "__main__":
    process_all_files()
