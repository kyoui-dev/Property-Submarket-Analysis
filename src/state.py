from typing import TypedDict 

from pydantic import BaseModel
from langgraph.prebuilt.chat_agent_executor import AgentState


class State(TypedDict):
    address: str
    property_type: str
    subject_property: list[dict]
    sale_listings: list[dict]
    sale_comps: list[dict]
    sale_listings_stats: list[dict]
    rental_listings: list[dict]
    rental_comps: list[dict]
    rental_listings_stats: list[dict]
    demographic_stats: list[dict]
    draft_report: str
    final_report: str
    output_path: str


class AnalyzerState(AgentState):
    subject_property: list[dict]
    sale_listings: list[dict]
    sale_comps: list[dict]
    sale_listings_stats: list[dict]
    rental_listings: list[dict]
    rental_comps: list[dict]
    rental_listings_stats: list[dict]
    demographic_stats: list[dict]