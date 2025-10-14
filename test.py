import json

from src.graph import build_graph
from src.state import State
from config import DATA_DIR


workflow = build_graph()

with open(f"{DATA_DIR}/test_cases.json", "r") as f:
    test_cases = json.load(f)

for i, item in enumerate(test_cases):
    state = State(property_type=item["property_type"], address=item["address"])
    workflow.invoke(state)