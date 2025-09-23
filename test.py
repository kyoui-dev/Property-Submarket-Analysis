import json

from src.workflow import build_workflow
from src.state import State
from config import DATA_DIR


with open(f"{DATA_DIR}/test_cases.json", "r") as f:
    test_cases = json.load(f)

workflow = build_workflow()

for i, item in enumerate(test_cases, 1):
    print(f"----- Running test case {i} -----")
    state = State(property_type=item["property_type"], address=item["address"])
    workflow.invoke(state)