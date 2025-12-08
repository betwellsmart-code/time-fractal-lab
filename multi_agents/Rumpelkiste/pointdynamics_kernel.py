"""
PointDynamics Kernel v0.1
Reine mathematische Logik ohne Tools oder OpenAI.
"""

def pd_rate(series):
    return [series[i+1] - series[i] for i in range(len(series)-1)]

def pd_velocity(rate):
    return [rate[i+1] - rate[i] for i in range(len(rate)-1)]

def pd_acceleration(velocity):
    return [velocity[i+1] - velocity[i] for i in range(len(velocity)-1)]

def pd_impact(series):
    # Beispielhafte Impact-Metrik
    return sum(abs(series[i+1] - series[i]) for i in range(len(series)-1))

def pd_kernel_pipeline(data):
    """
    Hauptpipeline der mathematischen Kernlogik.
    Wird vom Tool-Agent (0.2) verwendet.
    """
    series = data.get("series", [])

    if not isinstance(series, list) or len(series) < 3:
        return {"error": "series must be a list with >= 3 elements"}

    rate = pd_rate(series)
    velocity = pd_velocity(rate)
    acceleration = pd_acceleration(velocity)
    impact = pd_impact(series)

    return {
        "rate": rate,
        "velocity": velocity,
        "acceleration": acceleration,
        "impact": impact,
        "input_length": len(series)
    }
