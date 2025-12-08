# --- SAHAM-LAB BOOTSTRAP ---
import sys, os

# Absoluter Pfad der Sandbox (eine Ebene über multi_agents)
SANDBOX_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Sicherstellen, dass der Pfad im Python-Importsystem ist
if SANDBOX_ROOT not in sys.path:
    sys.path.insert(0, SANDBOX_ROOT)

print("[BOOTSTRAP] Sandbox-Root aktiv:", SANDBOX_ROOT)
# ---------------------------------
