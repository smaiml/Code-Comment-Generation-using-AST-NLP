"""Initial security-agent adapter for the planned agentic workflow.

This file intentionally provides a narrow, testable integration point that
reuses the existing static security analyzer without introducing a full
multi-agent coordinator.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .ast_extractor import ModuleFeatures
from .context_analyzer import ContextGraph
from .security_analyzer import run_security_analysis


def run_security_agent(
    source_code: str,
    module_features: Optional[ModuleFeatures] = None,
    context_graph: Optional[ContextGraph] = None,
) -> Dict[str, Any]:
    """Run the existing security analysis and return a structured result.

    This adapter is intentionally small: it does not add a full agent system,
    but it exposes a reusable interface for a future Security Agent in the
    project's agentic architecture.
    """
    if module_features is None or context_graph is None:
        from .parser_module import parse_code
        from .ast_extractor import extract_features
        from .context_analyzer import analyze_context

        tree = parse_code(source_code)
        module_features = extract_features(tree, source_code=source_code)
        context_graph = analyze_context(module_features, tree, source_code)

    report = run_security_analysis(module_features, context_graph, source_code)
    findings = []
    for issue in report.issues:
        findings.append(
            {
                "pattern_id": issue.pattern_id,
                "severity": issue.severity,
                "function_name": issue.function_name,
                "message": issue.message,
                "line": issue.lineno,
                "remediation": issue.remediation,
            }
        )

    return {
        "total_issues": report.total_issues,
        "module_safe_pct": report.module_safe_pct,
        "severity_summary": report.by_severity,
        "security_findings": findings,
    }
