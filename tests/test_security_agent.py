import unittest

from src.parser_module import parse_code
from src.ast_extractor import extract_features
from src.context_analyzer import analyze_context
from src.security_agent import run_security_agent


SECURITY_CODE = '''
def run_user_expression(expr: str):
    eval(expr)


def shell_execute(cmd: str) -> str:
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout
'''


class TestSecurityAgent(unittest.TestCase):

    def test_run_security_agent_returns_structured_findings(self):
        tree = parse_code(SECURITY_CODE)
        module_features = extract_features(tree, source_code=SECURITY_CODE)
        context_graph = analyze_context(module_features, tree, SECURITY_CODE)

        payload = run_security_agent(SECURITY_CODE, module_features, context_graph)

        self.assertIn("total_issues", payload)
        self.assertIn("module_safe_pct", payload)
        self.assertIn("severity_summary", payload)
        self.assertIn("security_findings", payload)
        self.assertGreaterEqual(payload["total_issues"], 1)


if __name__ == "__main__":
    unittest.main()
