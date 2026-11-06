import unittest
from pathlib import Path
from utcp_forge.extractors.fastapi_ast import FastAPIASTExtractor
from utcp_forge.agent.investigator import RouteInvestigatorAgent
from utcp_forge.compiler.manual_builder import UtcpCompiler

class TestUTCPForgePipeline(unittest.TestCase):
    def test_ast_extractor_finds_routes(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        extractor = FastAPIASTExtractor(str(fixture_dir))
        routes = extractor.scan()

        paths = [r.path for r in routes]
        self.assertIn("/health", paths)
        self.assertIn("/metrics", paths)
        self.assertIn("/api/v1/users/{user_id}", paths)
        self.assertIn("/api/v1/orders", paths)

        order_route = next(r for r in routes if r.path == "/api/v1/orders")
        self.assertTrue(order_route.auth_required)
        self.assertEqual(order_route.auth_type, "bearer")

    def test_agent_investigation_and_utcp_compiler(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        extractor = FastAPIASTExtractor(str(fixture_dir))
        routes = extractor.scan()

        agent = RouteInvestigatorAgent()
        enriched = [agent.investigate(r) for r in routes]

        # Health & metrics should be pruned
        health_tool = next(t for t in enriched if t.path == "/health")
        self.assertFalse(health_tool.should_include)

        # Valid business tools should be included
        included = [t for t in enriched if t.should_include]
        self.assertEqual(len(included), 4)

        manual = UtcpCompiler.compile(enriched, base_url="https://api.mycompany.com")
        self.assertEqual(manual.manual_version, "1.0.0")
        self.assertEqual(manual.utcp_version, "1.0.2")
        self.assertEqual(len(manual.tools), 4)

        # Verify order tool protocol constraints & auth
        order_tool = next(t for t in manual.tools if t.name == "post_place_order")
        self.assertEqual(order_tool.tool_call_template.call_template_type, "http")
        self.assertEqual(order_tool.tool_call_template.allowed_communication_protocols, ["http"])
        self.assertIsNotNone(order_tool.tool_call_template.auth)

if __name__ == "__main__":
    unittest.main()
