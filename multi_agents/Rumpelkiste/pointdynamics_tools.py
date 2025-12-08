"""
PointDynamics 0.2 – Tool-Agent
Bindeglied zwischen OpenAI-Tool-Aufrufen und Kernel-Logik.
"""

from multi_agents.pointdynamics_kernel import pd_kernel_pipeline

def pointdynamics_full(series: list):
    """
    Wrapper für OpenAI-Tool-Aufruf.
    Erwartet ein Argument "series".
    """
    data = {"series": series}
    return pd_kernel_pipeline(data)


POINTDYNAMICS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "pointdynamics_full",
            "description": "Analyse zeitbasierter Bewegungs- und Veränderungsmuster",
            "parameters": {
                "type": "object",
                "properties": {
                    "series": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Zeitreihe numerischer Punktwerte"
                    }
                },
                "required": ["series"]
            }
        }
    }
]
