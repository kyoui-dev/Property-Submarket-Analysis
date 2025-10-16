import logging
import re
import base64

import streamlit as st

from src.state import State
from src.graph import build_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

workflow = build_graph()

st.title("Automated Property Submarket Analysis")

with st.form("property_form"):
    address = st.text_input("Address *", placeholder="e.g. 1824 Nw 32nd St, Oklahoma City, OK 73118")
    property_type = st.selectbox(
    "Property Type *",
    options=[
        "Single Family",
        "Condo",
        "Townhouse",
        "Manufactured",
        "Multi-Family",
        "Apartment",
        "Land"
        ]
    )
    submitted = st.form_submit_button("Submit")
    
if submitted:
    if not property_type or not address:
        st.error("Property Type and Address are required.")
    elif not re.match(r"^\d+\s+[\w\s]+\s*,\s*[\w\s]+\s*,\s*[A-Z]{2}\s*\d{5}$", address):
        st.error("Please enter the full property address in the format: Street Address, City, State ZIP (e.g. 44 Croteau Ct , Manchester, NH 03104)")
    else:
        with st.spinner("Generating report..."):
            try:
                logger.info("Workflow started.")
                state = workflow.invoke(State(address=address, property_type=property_type))
                logger.info("Workflow completed.")

                with open(state["output_path"], "rb") as f:
                    pdf_base64 = base64.b64encode(f.read()).decode()

                st.markdown(f"<iframe src=\"data:application/pdf;base64,{pdf_base64}\" width=\"700\" height=\"1000\" type=\"application/pdf\"></iframe>", unsafe_allow_html=True)

            except Exception as e:
                logger.exception("Workflow failed.")
                st.error("An error occurred during report generation.")
                raise