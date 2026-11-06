import unittest
from pathlib import Path
from utcp_forge.extractors.fastapi_ast import FastAPIASTExtractor
from utcp_forge.indexer.symbol_table import SymbolTable
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

    def test_symbol_table_resolution(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        table = SymbolTable(str(fixture_dir))
        self.assertIn("UserCreate", table.models)
        self.assertIn("OrderPayload", table.models)

        schema = table.resolve_model_schema("OrderPayload")
        self.assertIsNotNone(schema)
        self.assertIn("item_id", schema["properties"])
        self.assertIn("quantity", schema["properties"])

    def test_namespaced_utcp_compilation(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        table = SymbolTable(str(fixture_dir))
        extractor = FastAPIASTExtractor(str(fixture_dir))
        routes = extractor.scan()

        agent = RouteInvestigatorAgent(symbol_table=table)
        enriched = [agent.investigate(r) for r in routes]

        # Compile with manual namespace 'store_api'
        manual = UtcpCompiler.compile(
            enriched,
            manual_name="store_api",
            base_url="https://api.store.com"
        )
        self.assertEqual(manual.manual_version, "1.0.0")
        self.assertEqual(manual.utcp_version, "1.0.2")

        # Verify expert namespacing: store_api.<resource>_<action>
        tool_names = [t.name for t in manual.tools]
        self.assertTrue(any(name.startswith("store_api.users_") for name in tool_names))
        self.assertTrue(any(name.startswith("store_api.orders_") for name in tool_names))

        # Verify auth variable namespacing: store_api__<VAR>
        auth_tool = next(t for t in manual.tools if "orders_create" in t.name)
        self.assertEqual(auth_tool.tool_call_template.auth.api_key, "Bearer ${store_api__API_KEY}")

if __name__ == "__main__":
    unittest.main()
