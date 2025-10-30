from langgraph.graph import StateGraph, START, END

from src.state import State
from src.nodes import (
    subject_property_collector,
    sale_listings_collector,
    rental_listings_collector,
    demographic_stats_collector,
    subject_property_processor,
    sale_listings_processor,
    rental_listings_processor,
    demographic_stats_processor,
    draft_report_generator,
    final_report_generator,
    pdf_converter
)


def build_graph():
    builder = StateGraph(State)

    builder.add_node("subject_property_collector", subject_property_collector)
    builder.add_node("sale_listings_collector", sale_listings_collector)
    builder.add_node("rental_listings_collector", rental_listings_collector)
    builder.add_node("demographic_stats_collector", demographic_stats_collector)
    builder.add_node("subject_property_processor", subject_property_processor)
    builder.add_node("sale_listings_processor", sale_listings_processor)
    builder.add_node("rental_listings_processor", rental_listings_processor)
    builder.add_node("demographic_stats_processor", demographic_stats_processor)
    builder.add_node("draft_report_generator", draft_report_generator)
    builder.add_node("final_report_generator", final_report_generator)
    builder.add_node("pdf_converter", pdf_converter)
    
    builder.add_edge(START, "subject_property_collector")
    builder.add_edge(START, "sale_listings_collector")
    builder.add_edge(START, "rental_listings_collector")
    builder.add_edge(START, "demographic_stats_collector")
    builder.add_edge("subject_property_collector", "subject_property_processor")
    builder.add_edge("subject_property_collector", "sale_listings_processor")
    builder.add_edge("subject_property_collector", "rental_listings_processor")
    builder.add_edge("sale_listings_collector", "sale_listings_processor")
    builder.add_edge("rental_listings_collector", "rental_listings_processor")
    builder.add_edge("demographic_stats_collector", "demographic_stats_processor")
    builder.add_edge("subject_property_processor", "draft_report_generator")
    builder.add_edge("sale_listings_processor", "draft_report_generator")
    builder.add_edge("rental_listings_processor", "draft_report_generator")
    builder.add_edge("demographic_stats_processor", "draft_report_generator")
    builder.add_edge("draft_report_generator", "final_report_generator")
    builder.add_edge("final_report_generator", "pdf_converter")
    builder.add_edge("pdf_converter", END)

    return builder.compile()