from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    ROOT / "observability.py": ["from app import", "import app"],
    ROOT / "static" / "app.js": ["SENTRY_DSN", "OTEL_EXPORTER", "API_KEY"],
}


def main() -> None:
    violations = []
    for path, forbidden in RULES.items():
        content = path.read_text(encoding="utf-8")
        violations.extend(f"{path.relative_to(ROOT)} contains forbidden dependency/token: {token}" for token in forbidden if token in content)
    if violations:
        raise SystemExit("\n".join(violations))
    print("Architecture contracts passed.")


if __name__ == "__main__":
    main()
