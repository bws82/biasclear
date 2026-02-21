"""
BiasClear Scan Certificate

Generates verifiable, shareable proof that a text was analyzed for
structural bias. Each certificate is:
  - Tied to a specific audit chain entry (SHA-256 hash)
  - Self-contained HTML with all scan results
  - Verifiable via GET /certificate/verify/{hash}

This is the "SSL certificate for text honesty."

Usage:
    from biasclear.certificate import generate_certificate_html, compute_certificate_id
    cert_id = compute_certificate_id(text, timestamp)
    html = generate_certificate_html(text, scan_result, audit_hash, cert_id, timestamp, verify_url)
"""

from __future__ import annotations

import hashlib
from html import escape


def generate_certificate_html(
    text: str,
    scan_result: dict,
    audit_hash: str,
    certificate_id: str,
    issued_at: str,
    verify_url: str,
) -> str:
    """Generate a self-contained HTML certificate for a bias scan."""

    truth_score = scan_result.get("truth_score", 0)
    flags = scan_result.get("flags", [])
    flag_count = len(flags)
    domain = escape(str(scan_result.get("domain", "general")))
    pit_tier = escape(str(scan_result.get("pit_tier", "none")))
    bias_detected = scan_result.get("bias_detected", flag_count > 0)

    # Determine status
    if not bias_detected:
        status = "CLEAN"
        status_color = "#10b981"
        status_icon = "&#10003;"
        status_text = "No structural bias detected"
    elif truth_score >= 70:
        status = "LOW RISK"
        status_color = "#f59e0b"
        status_icon = "&#9888;"
        status_text = f"{flag_count} minor pattern{'s' if flag_count != 1 else ''} detected"
    else:
        status = "BIAS DETECTED"
        status_color = "#ef4444"
        status_icon = "&#10007;"
        status_text = f"{flag_count} structural distortion{'s' if flag_count != 1 else ''} detected"

    # Build flags HTML
    flags_html = ""
    if flags:
        for f in flags[:10]:  # Cap display at 10
            flag_name = escape(str(
                f.get("pattern_id", f.get("name", f.get("pattern", "Unknown")))
            ))
            flag_match = escape(str(f.get("matched_text", f.get("description", ""))))
            severity = f.get("severity", "moderate")
            pit = escape(str(f.get("pit_tier", "")))
            sev_color = {
                "low": "#94a3b8",
                "moderate": "#f59e0b",
                "high": "#ef4444",
                "critical": "#dc2626",
            }.get(severity, "#94a3b8")
            pit_html = (
                f'<span style="font-size:10px;color:#8b5cf6;margin-left:8px;">{pit}</span>'
                if pit else ""
            )
            match_html = (
                f'<div style="font-size:12px;color:#94a3b8;margin-top:2px;">'
                f'&ldquo;{flag_match}&rdquo;</div>'
                if flag_match else ""
            )
            flags_html += f"""
            <div style="border-left:3px solid {sev_color};padding:8px 12px;margin:6px 0;
                        background:rgba(255,255,255,0.03);border-radius:0 4px 4px 0;">
                <div style="font-weight:600;font-size:13px;color:#e2e8f0;">
                    {flag_name}{pit_html}
                </div>
                {match_html}
                <div style="font-size:11px;color:{sev_color};margin-top:4px;
                            text-transform:uppercase;">{escape(severity)}</div>
            </div>"""
    else:
        flags_html = (
            '<div style="color:#10b981;padding:12px;text-align:center;">'
            '&#10003; No distortions detected</div>'
        )

    # Truncate text for display and escape HTML
    display_text = escape(text[:500] + ("..." if len(text) > 500 else ""))

    # Score gauge percentage
    score_pct = max(0, min(100, truth_score))

    # Sanitize inputs for the template
    safe_cert_id = escape(certificate_id[:16])
    safe_issued = escape(issued_at[:19].replace("T", " "))
    safe_audit_hash = escape(audit_hash)
    safe_verify_url = escape(verify_url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BiasClear Certificate</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{
    font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
    background:#0a0a0f;color:#e2e8f0;min-height:100vh;
    display:flex;justify-content:center;padding:40px 20px;
  }}
  .certificate{{
    max-width:680px;width:100%;
    background:linear-gradient(145deg,#12121a 0%,#0d0d14 100%);
    border:1px solid rgba(139,92,246,0.2);border-radius:16px;overflow:hidden;
    box-shadow:0 0 60px rgba(139,92,246,0.08);
  }}
  .header{{
    background:linear-gradient(135deg,rgba(139,92,246,0.15) 0%,rgba(59,130,246,0.1) 100%);
    padding:32px;text-align:center;border-bottom:1px solid rgba(139,92,246,0.15);
  }}
  .header h1{{font-size:14px;font-weight:600;letter-spacing:3px;text-transform:uppercase;
    color:#8b5cf6;margin-bottom:8px;}}
  .header h2{{font-size:28px;font-weight:700;color:#f8fafc;}}
  .status-badge{{
    display:inline-flex;align-items:center;gap:8px;margin-top:16px;
    padding:8px 20px;border-radius:24px;font-size:14px;font-weight:600;
    letter-spacing:1px;background:rgba(0,0,0,0.3);
    border:1px solid {status_color}40;color:{status_color};
  }}
  .body{{padding:28px 32px;}}
  .section{{margin-bottom:24px;}}
  .section-title{{font-size:11px;font-weight:600;letter-spacing:2px;
    text-transform:uppercase;color:#64748b;margin-bottom:10px;}}
  .score-container{{display:flex;align-items:center;gap:20px;}}
  .score-ring{{width:80px;height:80px;position:relative;}}
  .score-ring svg{{transform:rotate(-90deg);}}
  .score-ring .value{{position:absolute;top:50%;left:50%;
    transform:translate(-50%,-50%) rotate(0deg);
    font-size:22px;font-weight:700;color:#f8fafc;}}
  .meta-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
  .meta-item{{background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;
    border:1px solid rgba(255,255,255,0.05);}}
  .meta-label{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;}}
  .meta-value{{font-size:14px;font-weight:500;color:#e2e8f0;margin-top:4px;
    word-break:break-all;}}
  .text-preview{{background:rgba(0,0,0,0.3);padding:16px;border-radius:8px;
    font-size:13px;line-height:1.6;color:#94a3b8;
    border:1px solid rgba(255,255,255,0.05);max-height:200px;overflow-y:auto;}}
  .footer{{padding:20px 32px;background:rgba(0,0,0,0.2);
    border-top:1px solid rgba(255,255,255,0.05);text-align:center;}}
  .verify-link{{display:inline-flex;align-items:center;gap:6px;
    color:#8b5cf6;text-decoration:none;font-size:13px;font-weight:500;}}
  .verify-link:hover{{text-decoration:underline;}}
  .hash{{font-family:'SF Mono','Fira Code',monospace;font-size:11px;
    color:#64748b;margin-top:8px;word-break:break-all;}}
  @media print{{
    body{{background:white;color:#1a1a2e;}}
    .certificate{{border-color:#ddd;box-shadow:none;}}
    .header{{background:#f5f3ff;}}
  }}
</style>
</head>
<body>
<div class="certificate">
  <div class="header">
    <h1>BiasClear</h1>
    <h2>Scan Certificate</h2>
    <div class="status-badge">
      <span style="font-size:18px;">{status_icon}</span>
      <span>{status}</span>
    </div>
  </div>
  <div class="body">
    <div class="section">
      <div class="section-title">Truth Alignment Score</div>
      <div class="score-container">
        <div class="score-ring">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.05)"
                    stroke-width="6"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="{status_color}"
                    stroke-width="6" stroke-dasharray="{score_pct * 2.136} 213.6"
                    stroke-linecap="round"/>
          </svg>
          <div class="value">{truth_score}</div>
        </div>
        <div>
          <div style="font-size:15px;font-weight:500;color:#e2e8f0;">{status_text}</div>
          <div style="font-size:12px;color:#64748b;margin-top:4px;">
            PIT Tier: {pit_tier} &middot; Domain: {domain}
          </div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="section-title">Structural Analysis ({flag_count} pattern{'s' if flag_count != 1 else ''})</div>
      {flags_html}
    </div>
    <div class="section">
      <div class="section-title">Scanned Text</div>
      <div class="text-preview">{display_text}</div>
    </div>
    <div class="section">
      <div class="section-title">Certificate Details</div>
      <div class="meta-grid">
        <div class="meta-item">
          <div class="meta-label">Certificate ID</div>
          <div class="meta-value">{safe_cert_id}...</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Issued</div>
          <div class="meta-value">{safe_issued} UTC</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Domain</div>
          <div class="meta-value">{domain}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Text Length</div>
          <div class="meta-value">{len(text):,} characters</div>
        </div>
      </div>
    </div>
  </div>
  <div class="footer">
    <a href="{safe_verify_url}" class="verify-link" target="_blank">
      &#128279; Verify this certificate
    </a>
    <div class="hash">SHA-256: {safe_audit_hash}</div>
  </div>
</div>
</body>
</html>"""


def compute_certificate_id(text: str, timestamp: str) -> str:
    """Deterministic certificate ID from text content + timestamp."""
    content = f"{text}{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()
