"""
Data Quality & Validation Engine
Implements Great Expectations-style validation rules without the dependency.
Covers: null checks, type validation, range checks, uniqueness, PII detection,
format consistency, anomaly detection, and schema drift detection.
"""

import re
import hashlib
from datetime import datetime


# ── PII Detection Patterns ──────────────────────────────────────
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

PII_COLUMN_NAMES = {
    "email", "e_mail", "email_address", "mail",
    "phone", "phone_number", "mobile", "cell", "telephone",
    "ssn", "social_security", "social_security_number",
    "credit_card", "card_number", "cc_number", "card_num",
    "address", "street_address", "home_address",
    "name", "first_name", "last_name", "full_name",
    "dob", "date_of_birth", "birth_date", "birthday",
    "passport", "passport_number", "driver_license",
    "salary", "income", "wage",
}


def run_data_quality_checks(data_profile: dict, previous_profile: dict = None) -> dict:
    """
    Run comprehensive data quality checks on a data profile.
    Returns categorized issues with severity levels.
    """
    checks = []
    score_deductions = 0

    columns = data_profile.get("columns", [])
    row_count = data_profile.get("row_count", 0)
    duplicate_rows = data_profile.get("duplicate_rows", 0)

    # ── Check 1: Null Analysis ──────────────────────────────────
    for col in columns:
        null_pct = col.get("null_percent", 0)
        if null_pct > 50:
            checks.append({
                "category": "data_quality",
                "severity": "critical",
                "rule": "null_threshold",
                "column": col["name"],
                "description": f"Column '{col['name']}' has {null_pct}% null values (>{50}% threshold)",
                "recommendation": "Drop column, impute values, or investigate upstream source",
                "detected": True,
            })
            score_deductions += 15
        elif null_pct > 20:
            checks.append({
                "category": "data_quality",
                "severity": "warning",
                "rule": "null_threshold",
                "column": col["name"],
                "description": f"Column '{col['name']}' has {null_pct}% null values",
                "recommendation": "Consider imputation strategy (mean/median/mode/forward-fill)",
                "detected": True,
            })
            score_deductions += 5
        elif null_pct > 0:
            checks.append({
                "category": "data_quality",
                "severity": "info",
                "rule": "null_threshold",
                "column": col["name"],
                "description": f"Column '{col['name']}' has {null_pct}% null values",
                "recommendation": "Handle nulls in ETL transformation",
                "detected": True,
            })

    # ── Check 2: Duplicate Detection ────────────────────────────
    if row_count > 0:
        dup_pct = round((duplicate_rows / row_count) * 100, 2)
        if dup_pct > 10:
            checks.append({
                "category": "data_quality",
                "severity": "critical",
                "rule": "duplicate_threshold",
                "column": "_all_",
                "description": f"{duplicate_rows} duplicate rows ({dup_pct}% of data)",
                "recommendation": "Implement deduplication with MERGE/UPSERT strategy",
                "detected": True,
            })
            score_deductions += 15
        elif dup_pct > 0:
            checks.append({
                "category": "data_quality",
                "severity": "warning",
                "rule": "duplicate_threshold",
                "column": "_all_",
                "description": f"{duplicate_rows} duplicate rows ({dup_pct}%)",
                "recommendation": "Add deduplication step in ETL pipeline",
                "detected": True,
            })
            score_deductions += 5

    # ── Check 3: Type Consistency ───────────────────────────────
    for col in columns:
        if col.get("semantic_type") == "string":
            samples = col.get("sample_values", [])
            numeric_count = sum(1 for s in samples if _is_numeric(s))
            if numeric_count > len(samples) * 0.5 and len(samples) > 2:
                checks.append({
                    "category": "data_quality",
                    "severity": "warning",
                    "rule": "type_consistency",
                    "column": col["name"],
                    "description": f"Column '{col['name']}' detected as string but contains mostly numeric values",
                    "recommendation": "Cast to numeric type in ETL step",
                    "detected": True,
                })
                score_deductions += 3

    # ── Check 4: Cardinality Analysis ───────────────────────────
    for col in columns:
        unique_count = col.get("unique_count", 0)
        if row_count > 0 and unique_count == row_count and col.get("semantic_type") not in ("integer",):
            checks.append({
                "category": "data_quality",
                "severity": "info",
                "rule": "high_cardinality",
                "column": col["name"],
                "description": f"Column '{col['name']}' has 100% unique values — potential primary key",
                "recommendation": "Consider using as primary key or unique identifier",
                "detected": True,
            })
        elif row_count > 0 and unique_count == 1:
            checks.append({
                "category": "data_quality",
                "severity": "warning",
                "rule": "low_cardinality",
                "column": col["name"],
                "description": f"Column '{col['name']}' has only 1 unique value — zero information content",
                "recommendation": "Consider dropping this column",
                "detected": True,
            })
            score_deductions += 3

    # ── Check 5: Numeric Range Anomalies ────────────────────────
    for col in columns:
        if col.get("semantic_type") in ("integer", "float"):
            col_min = col.get("min")
            col_max = col.get("max")
            col_mean = col.get("mean")
            col_std = col.get("std")

            if col_min is not None and col_max is not None and col_std is not None and col_std > 0:
                if col_max > col_mean + 5 * col_std or col_min < col_mean - 5 * col_std:
                    checks.append({
                        "category": "data_quality",
                        "severity": "warning",
                        "rule": "outlier_detection",
                        "column": col["name"],
                        "description": f"Column '{col['name']}' has extreme outliers (range: {col_min}–{col_max}, mean: {col_mean}, std: {col_std})",
                        "recommendation": "Add outlier capping/removal in ETL or flag as anomaly",
                        "detected": True,
                    })
                    score_deductions += 5

            # Negative values in typically positive columns
            if col_min is not None and col_min < 0:
                name_lower = col["name"].lower()
                if any(kw in name_lower for kw in ("price", "amount", "quantity", "count", "age", "revenue", "sales")):
                    checks.append({
                        "category": "data_quality",
                        "severity": "warning",
                        "rule": "negative_values",
                        "column": col["name"],
                        "description": f"Column '{col['name']}' has negative values (min={col_min}) which may be invalid for this field type",
                        "recommendation": "Validate negative values — clip to 0 or flag as anomalies",
                        "detected": True,
                    })
                    score_deductions += 5

    # ── Check 6: PII Detection ──────────────────────────────────
    pii_found = detect_pii(columns)
    for pii_item in pii_found:
        checks.append({
            "category": "security",
            "severity": "critical",
            "rule": "pii_detected",
            "column": pii_item["column"],
            "description": f"Potential PII detected in '{pii_item['column']}': {pii_item['type']}",
            "recommendation": f"Apply {pii_item['remediation']} before storing in data warehouse",
            "detected": True,
        })
        score_deductions += 10

    # ── Check 7: Schema Drift (if previous profile exists) ──────
    if previous_profile:
        drift_issues = detect_schema_drift(data_profile, previous_profile)
        checks.extend(drift_issues)
        score_deductions += len(drift_issues) * 8

    # ── Check 8: Data Freshness ─────────────────────────────────
    for col in columns:
        if col.get("semantic_type") in ("datetime", "datetime_string"):
            samples = col.get("sample_values", [])
            try:
                dates = []
                for s in samples:
                    try:
                        dates.append(datetime.fromisoformat(str(s).replace("Z", "+00:00")))
                    except (ValueError, TypeError):
                        pass
                if dates:
                    max_date = max(dates)
                    days_old = (datetime.now() - max_date.replace(tzinfo=None)).days
                    if days_old > 365:
                        checks.append({
                            "category": "data_quality",
                            "severity": "warning",
                            "rule": "data_freshness",
                            "column": col["name"],
                            "description": f"Most recent date in '{col['name']}' is {days_old} days old",
                            "recommendation": "Verify data source is providing current data",
                            "detected": True,
                        })
            except Exception:
                pass

    # ── Calculate Quality Score ──────────────────────────────────
    quality_score = max(0, 100 - score_deductions)

    return {
        "checks": checks,
        "quality_score": quality_score,
        "total_checks": len(checks),
        "critical_count": sum(1 for c in checks if c["severity"] == "critical"),
        "warning_count": sum(1 for c in checks if c["severity"] == "warning"),
        "info_count": sum(1 for c in checks if c["severity"] == "info"),
        "pii_detected": len(pii_found) > 0,
        "pii_columns": [p["column"] for p in pii_found],
    }


def detect_pii(columns: list) -> list:
    """Detect potential PII in column names and sample values."""
    pii_items = []

    for col in columns:
        col_name = col["name"].lower().replace(" ", "_").replace("-", "_")

        # Check column name against known PII field names
        if col_name in PII_COLUMN_NAMES:
            pii_type = _classify_pii_name(col_name)
            pii_items.append({
                "column": col["name"],
                "type": pii_type,
                "detection_method": "column_name_match",
                "remediation": _get_pii_remediation(pii_type),
            })
            continue

        # Check sample values against PII regex patterns
        samples = col.get("sample_values", [])
        for sample in samples:
            sample_str = str(sample)
            for pii_type, pattern in PII_PATTERNS.items():
                if pattern.search(sample_str):
                    pii_items.append({
                        "column": col["name"],
                        "type": pii_type,
                        "detection_method": "value_pattern_match",
                        "remediation": _get_pii_remediation(pii_type),
                    })
                    break
            else:
                continue
            break

    return pii_items


def detect_schema_drift(current_profile: dict, previous_profile: dict) -> list:
    """Compare current data profile with a previous one to detect schema changes."""
    issues = []

    current_cols = {c["name"]: c for c in current_profile.get("columns", [])}
    previous_cols = {c["name"]: c for c in previous_profile.get("columns", [])}

    # Check for new columns
    new_cols = set(current_cols.keys()) - set(previous_cols.keys())
    for col in new_cols:
        issues.append({
            "category": "schema_drift",
            "severity": "warning",
            "rule": "new_column",
            "column": col,
            "description": f"New column '{col}' detected (not in previous schema)",
            "recommendation": "Update pipeline to handle new column or ignore it",
            "detected": True,
        })

    # Check for removed columns
    removed_cols = set(previous_cols.keys()) - set(current_cols.keys())
    for col in removed_cols:
        issues.append({
            "category": "schema_drift",
            "severity": "critical",
            "rule": "removed_column",
            "column": col,
            "description": f"Column '{col}' was removed from the data source",
            "recommendation": "Update pipeline — downstream dependencies may break",
            "detected": True,
        })

    # Check for type changes
    for col_name in set(current_cols.keys()) & set(previous_cols.keys()):
        curr = current_cols[col_name]
        prev = previous_cols[col_name]
        if curr.get("dtype") != prev.get("dtype"):
            issues.append({
                "category": "schema_drift",
                "severity": "critical",
                "rule": "type_change",
                "column": col_name,
                "description": f"Column '{col_name}' type changed: {prev['dtype']} → {curr['dtype']}",
                "recommendation": "Update type casting in ETL pipeline",
                "detected": True,
            })

        # Check for significant null rate changes
        curr_null = curr.get("null_percent", 0)
        prev_null = prev.get("null_percent", 0)
        if abs(curr_null - prev_null) > 20:
            issues.append({
                "category": "schema_drift",
                "severity": "warning",
                "rule": "null_rate_change",
                "column": col_name,
                "description": f"Column '{col_name}' null rate changed significantly: {prev_null}% → {curr_null}%",
                "recommendation": "Investigate upstream data source for quality regression",
                "detected": True,
            })

    return issues


def mask_pii_value(value: str, pii_type: str) -> str:
    """Mask a PII value for safe display/logging."""
    if not value:
        return value
    s = str(value)
    if pii_type == "email":
        parts = s.split("@")
        if len(parts) == 2:
            return parts[0][:2] + "***@" + parts[1]
    elif pii_type in ("phone", "ssn", "credit_card"):
        return s[:2] + "*" * (len(s) - 4) + s[-2:]
    return s[:2] + "*" * max(0, len(s) - 4) + s[-2:] if len(s) > 4 else "***"


def hash_pii_value(value: str) -> str:
    """One-way hash a PII value for pseudonymization."""
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]


# ── Private Helpers ─────────────────────────────────────────────

def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _classify_pii_name(name: str) -> str:
    if name in ("email", "e_mail", "email_address", "mail"):
        return "email"
    if name in ("phone", "phone_number", "mobile", "cell", "telephone"):
        return "phone"
    if name in ("ssn", "social_security", "social_security_number"):
        return "ssn"
    if name in ("credit_card", "card_number", "cc_number", "card_num"):
        return "credit_card"
    if name in ("name", "first_name", "last_name", "full_name"):
        return "personal_name"
    if name in ("address", "street_address", "home_address"):
        return "address"
    if name in ("dob", "date_of_birth", "birth_date", "birthday"):
        return "date_of_birth"
    if name in ("salary", "income", "wage"):
        return "financial"
    return "potential_pii"


def _get_pii_remediation(pii_type: str) -> str:
    remediation_map = {
        "email": "hash or tokenize (SHA-256 pseudonymization)",
        "phone": "mask (show last 4 digits only)",
        "ssn": "encrypt at rest (AES-256) and mask in transit",
        "credit_card": "tokenize via PCI-DSS compliant vault",
        "personal_name": "pseudonymize or remove if not needed",
        "address": "generalize to city/region level",
        "date_of_birth": "generalize to age range or birth year",
        "ip_address": "anonymize (zero last octet)",
        "financial": "encrypt at rest and restrict access via IAM",
        "potential_pii": "review and apply appropriate masking/encryption",
    }
    return remediation_map.get(pii_type, "apply appropriate data protection")
