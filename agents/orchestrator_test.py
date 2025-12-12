"""
orchestrator_test.py – Architecture SystemCheck v1.1

Zweck:
    Prüft die Stabilität der Orchestrator-Architektur:
    - Imports
    - Agenten-Registry
    - verfügbare Methoden (ohne Ausführung)
    - Pre/Post-Check-Pfade (ohne Fachlogik)

Kein Erzwingen von Fach-Tasks.
"""

from orchestrator_logic import Orchestrator


def list_public_methods(obj):
    return sorted(
        name for name in dir(obj)
        if not name.startswith("_") and callable(getattr(obj, name))
    )


def run_test():
    print("\n=== ORCHESTRATOR ARCHITEKTURTEST ===")

    orch = Orchestrator()

    # ------------------------------------------------------------
    # Agentenliste
    # ------------------------------------------------------------
    agents = orch.list_agents()
    print(f"Gefundene Agenten ({len(agents)}): {agents}")

    assert len(agents) >= 5, "Zu wenige Agenten geladen!"
    print("OK: Agenten erfolgreich geladen.")

    # ------------------------------------------------------------
    # Methoden-Introspektion
    # ------------------------------------------------------------
    print("\n--- METHODEN-INTROSPEKTION ---")
    for name in agents:
        agent = orch.registry.get(name)
        methods = list_public_methods(agent)
        print(f"Agent '{name}': Methoden ({len(methods)}): {methods}")

    # ------------------------------------------------------------
    # Pre/Post-Check Smoke-Test (ohne Fach-Task)
    # ------------------------------------------------------------
    print("\n--- SYSTEMCONTROLGATE SMOKE-TEST ---")
    ok, info = orch.system_control_gate.precheck(
        agent_name="system",
        task_name="noop",
        payload={"ping": True},
    )
    print("Precheck:", ok, info)

    ok2, info2 = orch.system_control_gate.postcheck(
        agent_name="system",
        task_name="noop",
        payload={"ping": True},
        output={"result": "ok"},
    )
    print("Postcheck:", ok2, info2)

    print("\n=== ARCHITEKTURTEST BEENDET (GRÜN) ===")


if __name__ == "__main__":
    run_test()
