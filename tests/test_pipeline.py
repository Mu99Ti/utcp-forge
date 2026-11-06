import unittest
from pathlib import Path
from utcp_forge.extractors.fastapi_ast import FastAPIASTExtractor
from utcp_forge.indexer.symbol_table import SymbolTable
from utcp_forge.indexer.host_detector import HostDetector
from utcp_forge.agent.investigator import RouteInvestigatorAgent
from utcp_forge.compiler.manual_builder import UtcpCompiler
from utcp_forge.models.ir import EnrichedToolIR

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

        user_route = next(r for r in routes if r.path == "/api/v1/users/{user_id}")
        user_id_param = next(p for p in user_route.params if p.name == "user_id")
        self.assertEqual(user_id_param.location, "path")

    def test_symbol_table_resolution(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        table = SymbolTable(str(fixture_dir))
        self.assertIn("UserCreate", table.models)
        self.assertIn("OrderPayload", table.models)

        schema = table.resolve_model_schema("OrderPayload")
        self.assertIsNotNone(schema)
        self.assertIn("item_id", schema["properties"])
        self.assertIn("quantity", schema["properties"])

    def test_host_detector(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_app"
        base_url = HostDetector.detect_base_url(str(fixture_dir), default="http://localhost:9000")
        self.assertEqual(base_url, "http://localhost:9000")

    def test_namespaced_utcp_compilation_and_collision_handling(self):
        tools = [
            EnrichedToolIR(
                name="get_users",
                path="/users",
                method="GET",
                description="List all users",
                intent="list_users",
                should_include=True
            ),
            EnrichedToolIR(
                name="get_users_duplicate",
                path="/users",
                method="GET",
                description="List all users duplicate",
                intent="list_users_2",
                should_include=True
            ),
            EnrichedToolIR(
                name="create_order",
                path="/orders",
                method="POST",
                description="Place an order",
                intent="create_order",
                auth_header="Authorization",
                auth_env_var="API_KEY",
                should_include=True
            )
        ]

        manual = UtcpCompiler.compile(tools, manual_name="store_api", base_url="https://api.store.com")
        self.assertEqual(manual.manual_version, "1.0.0")
        self.assertEqual(manual.utcp_version, "1.0.2")

        tool_names = [t.name for t in manual.tools]
        self.assertIn("store_api.users_list", tool_names)
        self.assertIn("store_api.users_list_2", tool_names)
        self.assertIn("store_api.orders_create", tool_names)

        # Check URL formatting has single slash
        order_tool = next(t for t in manual.tools if t.name == "store_api.orders_create")
        self.assertEqual(order_tool.tool_call_template.url, "https://api.store.com/orders")
        self.assertEqual(order_tool.tool_call_template.auth.api_key, "Bearer ${store_api__API_KEY}")

if __name__ == "__main__":
    unittest.main()
