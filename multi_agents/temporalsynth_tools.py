def ts_full_pipeline(**kwargs):
    return {"agent": "TemporalSynth", "status": "dummy-run"}

TEMPORALSYNTH_TOOLS = [{
    "type": "function",
    "function": {"name": "temporal_full", "description": "Dummy", "parameters": {"type": "object","properties": {}}}
}]
