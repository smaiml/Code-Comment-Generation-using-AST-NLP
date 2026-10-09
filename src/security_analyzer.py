import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .ast_extractor import ModuleFeatures, FunctionFeature
from .context_analyzer import FunctionContext, VariableInfo


class SecurityError(RuntimeError):
    """Raised when a module fails the malware and vulnerability gate."""

    def __init__(self, message: str, report: "SecurityReport"):
        super().__init__(message)
        self.report = report


def enforce_security_gate(report: "SecurityReport") -> None:
    """Raise when critical malware or a low module safety score is found."""
    if any(issue.severity == "critical" for issue in report.issues) or report.module_safe_pct < 80.0:
        raise SecurityError(
            "CRITICAL MALWARE / VULNERABILITY DETECTED: Execution aborted.",
            report,
        )


@dataclass
class SecurityIssue:
    pattern_id: str
    severity: str
    function_name: str
    message: str
    lineno: int = 0
    remediation: str = ""


@dataclass
class SecurityReport:
    function_scores: Dict[str, float] = field(default_factory=dict)
    module_safe_pct: float = 100.0
    total_issues: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    issues: List[SecurityIssue] = field(default_factory=list)

    def add_issue(self, issue: SecurityIssue):
        self.issues.append(issue)
        self.total_issues += 1
        self.by_severity[issue.severity] = self.by_severity.get(issue.severity, 0) + 1

    def compute_function_score(self, func_name: str, issues: List[SecurityIssue]) -> float:
        weights = {"critical": 30, "high": 15, "medium": 5, "low": 1}
        penalty = sum(weights.get(i.severity, 0) for i in issues)
        return max(0.0, min(100.0, 100.0 - penalty))

    def compute_module_safe_pct(self, all_scores: Dict[str, float]) -> float:
        if not all_scores:
            return 100.0
        return round(sum(all_scores.values()) / len(all_scores), 1)

    def to_dict(self) -> dict:
        return {
            "function_scores": self.function_scores,
            "module_safe_pct": self.module_safe_pct,
            "total_issues": self.total_issues,
            "by_severity": self.by_severity,
            "issues": [
                {
                    "pattern_id": i.pattern_id,
                    "severity": i.severity,
                    "function_name": i.function_name,
                    "message": i.message,
                    "lineno": i.lineno,
                    "remediation": i.remediation,
                }
                for i in self.issues
            ],
        }


_UNSAFE_BUILTINS = {"eval", "exec", "compile"}
_WEAK_CRYPTO = {"hashlib.md5", "hashlib.sha1", "md5", "sha1", "MD5", "SHA1",
                "Crypto.Hash.MD5", "Crypto.Hash.SHA"}
_SQL_CONCAT_PATTERNS = [
    re.compile(r'["\'].*\+.*["\']', re.IGNORECASE),
    re.compile(r'f["\'].*\{.*\}.*SELECT', re.IGNORECASE),
]
_DANGEROUS_DESERIALIZE = {"pickle.load", "pickle.loads", "cPickle.load",
                          "yaml.load", "yaml.unsafe_load"}
_INSECURE_RANDOM = {"random.randint", "random.random", "random.choice",
                    "random.randrange", "random.shuffle"}
_HARDCODED_SECRET_NAMES = {
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "access_key", "private_key", "auth_key", "credentials",
}
_MUTABLE_DEFAULTS = {"list", "dict", "set"}
_HARD_CODED_IP = re.compile(r'(?<!\w)(?:\d{1,3}\.){3}\d{1,3}(?!\w)')
_HARD_CODED_URL = re.compile(r'https?://[^\s"\']+')
_IP_LITERAL = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
_BOT_TOKEN = re.compile(r'\b\d{6,12}:[A-Za-z0-9_-]{30,}\b')
_SECRET_VALUE = re.compile(
    r'(?i)(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|'
    r'sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})'
)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _literal_string(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


class _HighRiskScanner(ast.NodeVisitor):
    """Collect requested malware indicators directly from Python syntax."""

    _SHELL_COMMANDS = {
        "subprocess.run", "subprocess.call", "subprocess.Popen",
        "subprocess.check_call", "subprocess.check_output",
    }
    _NETWORK_CALLS = {
        "socket.connect", "socket.create_connection", "requests.get",
        "requests.post", "httpx.get", "httpx.post", "urllib.request.urlopen",
    }

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.function_stack: List[str] = []
        self.module_aliases: Dict[str, str] = {}
        self.function_aliases: Dict[str, str] = {}
        self.function_network: Dict[str, bool] = {}
        self.function_ips: Dict[str, Dict[str, int]] = {}
        self.function_process_exec: Dict[str, bool] = {}
        self._seen: Set[tuple] = set()

    @property
    def current_function(self) -> str:
        return self.function_stack[-1] if self.function_stack else "<module>"

    def add(self, pattern_id: str, severity: str, message: str, node: ast.AST, remediation: str):
        function_name = self.current_function
        key = (pattern_id, function_name, getattr(node, "lineno", 0))
        if key in self._seen:
            return
        self._seen.add(key)
        self.issues.append(SecurityIssue(
            pattern_id=pattern_id,
            severity=severity,
            function_name=function_name,
            message=message,
            lineno=getattr(node, "lineno", 0),
            remediation=remediation,
        ))

    def scan(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.module_aliases[alias.asname or alias.name.split(".")[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    self.function_aliases[alias.asname or alias.name] = f"{module}.{alias.name}".strip(".")
        self.visit(tree)
        for function_name, has_network in self.function_network.items():
            if has_network and self.function_ips.get(function_name):
                ip_lines = self.function_ips[function_name]
                issue = SecurityIssue(
                    pattern_id="SEC014",
                    severity="high",
                    function_name=function_name,
                    message=("Network operation targets hardcoded IP address(es): "
                             + ", ".join(sorted(ip_lines)[:3])
                             + "; this may indicate a suspicious remote endpoint."),
                    lineno=min(ip_lines.values()),
                    remediation="Use trusted host configuration and validate destinations against an allowlist.",
                )
                self.issues.append(issue)
        for function_name, has_network in self.function_network.items():
            if has_network and self.function_process_exec.get(function_name):
                self.issues.append(SecurityIssue(
                    pattern_id="SEC013",
                    severity="critical",
                    function_name=function_name,
                    message="Function combines network communication with process execution, a reverse-shell indicator.",
                    remediation="Remove the behavior and investigate the source of the code.",
                ))
        return self.issues

    def _resolve(self, name: str) -> str:
        if name in self.function_aliases:
            return self.function_aliases[name]
        head, separator, tail = name.partition(".")
        if head in self.module_aliases:
            return self.module_aliases[head] + (separator + tail if separator else "")
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call):
        name = self._resolve(_call_name(node.func))
        short_name = name.rsplit(".", 1)[-1]
        if short_name in {"eval", "exec", "compile"} and name in {
            "eval", "exec", "compile", "builtins.eval", "builtins.exec", "builtins.compile"
        }:
            self.add("SEC001", "critical", f"Uses dangerous builtin '{short_name}' — allows arbitrary code execution.", node,
                     "Replace with a safe parser or a narrowly scoped allowlisted operation.")

        if name.startswith("subprocess.") or name.startswith(("os.exec", "os.spawn", "os.popen")):
            self.function_process_exec[self.current_function] = True

        if name == "os.system":
            self.function_process_exec[self.current_function] = True
            self.add("SEC002", "critical", "Uses os.system() to execute an operating-system command.", node,
                     "Use a fixed executable with an argument list and avoid shell interpretation.")

        if name in self._SHELL_COMMANDS:
            shell_true = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if shell_true:
                self.function_process_exec[self.current_function] = True
                self.add("SEC002", "critical", "Potential shell injection via subprocess with shell=True.", node,
                         "Use subprocess without shell=True and pass arguments as a list.")

        if name in {"pickle.load", "pickle.loads", "cPickle.load", "cPickle.loads"}:
            self.add("SEC009", "critical", f"Uses unsafe deserialization '{name}' — may execute arbitrary code.", node,
                     "Use a non-executable data format such as JSON for untrusted input.")
        if name in {"yaml.load", "yaml.unsafe_load", "yaml.load_all"}:
            loader = next((kw.value for kw in node.keywords if kw.arg == "Loader"), None)
            loader_name = self._resolve(_call_name(loader)) if loader is not None else ""
            safe_loader = loader_name in {"yaml.SafeLoader", "yaml.CSafeLoader"}
            if name != "yaml.unsafe_load" and not safe_loader:
                self.add("SEC010", "high", f"Uses unsafe YAML deserialization '{name}'.", node,
                         "Use yaml.safe_load() or explicitly specify yaml.SafeLoader.")
            elif name == "yaml.unsafe_load":
                self.add("SEC010", "high", "Uses yaml.unsafe_load() on potentially untrusted data.", node,
                         "Use yaml.safe_load() for untrusted YAML.")

        if (name in self._NETWORK_CALLS or name.startswith(("requests.", "httpx."))
                or name.endswith((".connect", ".connect_ex", ".create_connection"))):
            self.function_network[self.current_function] = True
            for argument in list(node.args) + [kw.value for kw in node.keywords]:
                value = _literal_string(argument)
                if value:
                    for ip_address in _IP_LITERAL.findall(value):
                        self.function_ips.setdefault(self.current_function, {})[ip_address] = getattr(node, "lineno", 0)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            for ip_address in _IP_LITERAL.findall(node.value):
                self.function_ips.setdefault(self.current_function, {})[ip_address] = node.lineno
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self._check_secret_assignment(node.targets, node.value, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is not None:
            self._check_secret_assignment([node.target], node.value, node)
        self.generic_visit(node)

    def _check_secret_assignment(self, targets, value, node):
        string_value = _literal_string(value)
        names = [target.id.lower() for target in targets if isinstance(target, ast.Name)]
        secret_name = any(any(marker in name for marker in _HARDCODED_SECRET_NAMES) for name in names)
        secret_value = bool(string_value and (_BOT_TOKEN.search(string_value) or _SECRET_VALUE.search(string_value)))
        if string_value and string_value.strip() and (secret_name or secret_value):
            target_name = next((target.id for target in targets if isinstance(target, ast.Name)), "credential")
            self.add("SEC003", "high", f"Potential hardcoded secret in variable '{target_name}'.", node,
                     "Load credentials from environment variables or a secrets manager.")


def run_security_analysis(
    module_features: ModuleFeatures,
    context_graph,
    source_code: str = "",
) -> SecurityReport:
    """
    Comprehensive security analysis of Python source code.

    Scans AST features and context for security anti-patterns,
    producing a SecurityReport with per-function scores and module safety %.
    """
    report = SecurityReport()
    fc_map: Dict[str, FunctionContext] = {
        fc.name: fc for fc in context_graph.function_contexts
    }

    source_lines = source_code.splitlines() if source_code else []
    if source_code:
        try:
            ast_tree = ast.parse(source_code)
            for issue in _HighRiskScanner().scan(ast_tree):
                report.add_issue(issue)
        except SyntaxError:
            pass

    for ff in module_features.functions:
        fc = fc_map.get(ff.name)
        func_issues: List[SecurityIssue] = []

        for call in ff.calls_made:
            for weak in _WEAK_CRYPTO:
                if weak in call:
                    func_issues.append(SecurityIssue(
                        pattern_id="SEC004",
                        severity="medium",
                        function_name=ff.name,
                        message=f"Uses weak cryptographic hash '{call}'.",
                        lineno=ff.lineno,
                        remediation="Use SHA-256 or stronger from hashlib.",
                    ))
                    break

            for rng in _INSECURE_RANDOM:
                if rng in call:
                    func_issues.append(SecurityIssue(
                        pattern_id="SEC011",
                        severity="medium",
                        function_name=ff.name,
                        message=f"Uses insecure random '{call}' — not suitable for cryptography.",
                        lineno=ff.lineno,
                        remediation="Use secrets module for security-sensitive randomness.",
                    ))
                    break

        if source_code:
            func_src = "\n".join(source_lines[ff.lineno - 1:ff.lineno + ff.body_lines])

            for pattern in _SQL_CONCAT_PATTERNS:
                if pattern.search(func_src) and ("SELECT" in func_src.upper() or "INSERT" in func_src.upper()):
                    func_issues.append(SecurityIssue(
                        pattern_id="SEC005",
                        severity="high",
                        function_name=ff.name,
                        message="Potential SQL injection via string concatenation.",
                        lineno=ff.lineno,
                        remediation="Use parameterized queries with placeholders.",
                    ))
                    break

            if re.search(r'\bexcept\s*:', func_src):
                func_issues.append(SecurityIssue(
                    pattern_id="SEC006",
                    severity="medium",
                    function_name=ff.name,
                    message="Bare 'except:' clause catches all exceptions including SystemExit and KeyboardInterrupt.",
                    lineno=ff.lineno,
                    remediation="Catch specific exceptions: except ValueError: or except Exception:",
                ))

            try:
                func_tree = ast.parse(func_src)
                for node in ast.walk(func_tree):
                    if isinstance(node, ast.FunctionDef):
                        for default in node.args.defaults:
                            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                func_issues.append(SecurityIssue(
                                    pattern_id="SEC007",
                                    severity="low",
                                    function_name=ff.name,
                                    message="Mutable default argument — shared across all calls.",
                                    lineno=ff.lineno,
                                    remediation="Use None as default and initialize inside the function.",
                                ))
                                break
            except SyntaxError:
                pass

            if "assert" in func_src and not any(
                name in ("test_", "_test", "_tests") for name in [ff.name[:5]]
            ):
                if re.search(r'\bassert\b', func_src):
                    func_issues.append(SecurityIssue(
                        pattern_id="SEC008",
                        severity="low",
                        function_name=ff.name,
                        message="assert statement used in non-test code — disabled with -O flag.",
                        lineno=ff.lineno,
                        remediation="Use explicit if/raise for runtime checks.",
                    ))

            ips = _HARD_CODED_IP.findall(func_src)
            if ips:
                func_issues.append(SecurityIssue(
                    pattern_id="SEC012",
                    severity="low",
                    function_name=ff.name,
                    message=f"Hardcoded IP address(es) found: {', '.join(ips[:3])}.",
                    lineno=ff.lineno,
                    remediation="Use configuration files or environment variables for host addresses.",
                ))

        for issue in func_issues:
            report.add_issue(issue)

        all_func_issues = [issue for issue in report.issues if issue.function_name == ff.name]
        score = report.compute_function_score(ff.name, all_func_issues)
        report.function_scores[ff.name] = score

    for issue in report.issues:
        if issue.function_name not in report.function_scores:
            report.function_scores[issue.function_name] = report.compute_function_score(
                issue.function_name,
                [finding for finding in report.issues if finding.function_name == issue.function_name],
            )

    report.module_safe_pct = report.compute_module_safe_pct(report.function_scores)
    return report
