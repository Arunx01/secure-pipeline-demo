import json
import sys
from collections import defaultdict

# Semgrep uses ERROR / WARNING / INFO; we translate to standard severity names
SEVERITY_MAP = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
ORDER = ["HIGH", "MEDIUM", "LOW"]

# Findings we reviewed and decided are false positives.
# Format: (part of rule name, file path)
IGNORE = []


def load_findings(path):
    with open(path) as f:
        data = json.load(f)
    return data.get("results", [])


def cwe_of(metadata):
    cwe = metadata.get("cwe", "n/a")
    if isinstance(cwe, list):
        cwe = cwe[0] if cwe else "n/a"
    return cwe.split(":")[0]


def is_ignored(finding):
    for rule_part, file_path in IGNORE:
        if rule_part in finding["check_id"] and finding["path"] == file_path:
            return True
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 triage.py semgrep-results.json")
        sys.exit(1)

    findings = load_findings(sys.argv[1])
    buckets = defaultdict(list)
    ignored = 0

    for finding in findings:
        if is_ignored(finding):
            ignored += 1
            continue
        severity = SEVERITY_MAP.get(finding["extra"]["severity"], "LOW")
        buckets[severity].append(finding)

    total = sum(len(v) for v in buckets.values())
    print("=" * 60)
    print(f"TRIAGE SUMMARY: {total} finding(s), {ignored} ignored as false positive")
    print("=" * 60)

    for severity in ORDER:
        items = buckets.get(severity, [])
        print(f"\n{severity}: {len(items)}")
        for f in items:
            rule = f["check_id"].split(".")[-1]
            line = f["start"]["line"]
            cwe = cwe_of(f["extra"].get("metadata", {}))
            print(f"  - {f['path']}:{line}  [{cwe}]  {rule}")


if __name__ == "__main__":
    main()
