from typing import Annotated 

from pydantic import BaseModel
from langgraph.graph.message import add_messages


class State(BaseModel):
    property_type: str
    address: str
    subject_property: list[dict] = None
    sale_listings: list[dict] = None
    sale_comps: list[dict] = None
    sale_listings_stats: list[dict] = None
    rental_listings: list[dict] = None
    rental_comps: list[dict] = None
    rental_listings_stats: list[dict] = None
    demographic_stats: list[dict] = None
    messages: Annotated[list, add_messages] = None
    remaining_steps: int = None
    draft_report: str = None
    final_report: str = None
    output_path: str = None


class AgentState(BaseModel):
    messages: Annotated[list, add_messages] = None
    remaining_steps: int = None
    subject_property: list[dict]
    sale_listings: list[dict]
    sale_comps: list[dict]
    sale_listings_stats: list[dict]
    rental_listings: list[dict]
    rental_comps: list[dict]
    rental_listings_stats: list[dict]
    demographic_stats: list[dict]