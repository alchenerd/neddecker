import threading

g_payload = {}
g_payload_lock = None
g_actions = []
g_actions_lock = None

g_payload_lock = threading.RLock()
g_actions_lock = threading.RLock()
