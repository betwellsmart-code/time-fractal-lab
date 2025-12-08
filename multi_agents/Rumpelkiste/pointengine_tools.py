def pe_full_pipeline(**kwargs):
    return {"agent": "PointEngine", "status": "dummy-run"}

POINTENGINE_TOOLS = [{
    "type": "function",
    "function": {"name": "pointengine_full", "description": "Dummy", "parameters": {"type": "object", "properties": {}}}
}]
