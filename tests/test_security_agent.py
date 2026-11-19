import unittest

from src.parser_module import parse_code
from src.ast_extractor import extract_features
from src.context_analyzer import analyze_context
from src.security_agent import run_security_agent


SECURITY_CODE = '''
import sqlite3
import subprocess

API_KEY = "sk_live_demo_9876543210_hardcoded_secret"

def find_user_by_name(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Potential SQL injection via string formatting (SEC004)
    query = f"SELECT id, username, role FROM users WHERE username = '{username}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def ping_host(host):
    # Potential OS command injection via shell=True (SEC002)
    completed = subprocess.run(f"ping -n 1 {host}", shell=True, capture_output=True, text=True)
    return completed.stdout
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
