from typing import Optional

def should_ticket(asset, vuln) -> bool:
    if (vuln.status or "").lower() in {"false_positive", "closed", "mitigated"}:
        return False

    try:
        score = float(vuln.cvss_score) if vuln.cvss_score is not None else None
    except (TypeError, ValueError):
        score = None

    if score is None:
        return False

    if score >= 9.0:
        sev = "critical"
    elif score >= 7.0:
        sev = "high"
    elif score >= 4.0:
        sev = "medium"
    else:
        sev = "low"

    if sev in {"critical", "high"}:
        return True

    if sev == "medium" and vuln.exploit_available:
        env = (getattr(asset, 'environment', '') or "").lower()
        if env == "prod":
            return True

    return False