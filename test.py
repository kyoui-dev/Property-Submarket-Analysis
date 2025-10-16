import json

from src.graph import build_graph
from src.state import State
from config import DATA_DIR

workflow = build_graph()

with open(f"{DATA_DIR}/test_cases.json", "r") as f:
    test_cases = json.load(f)

for test_case in test_cases:
    workflow.invoke(State(address=test_case["address"], property_type=test_case["property_type"]))