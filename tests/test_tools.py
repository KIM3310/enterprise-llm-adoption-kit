from app.tools import ToolRouter


def test_tool_allowlist_denies_unknown():
    router = ToolRouter(knowledge_search_fn=lambda q, r: {})
    result, status = router.call("unknown_tool", {}, "Employee")
    assert status == "denied"
    assert "error" in result
