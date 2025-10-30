import logging
import functools
import json
from uuid import uuid4

import requests
import pandas as pd
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from markdown_pdf import MarkdownPdf, Section

from src.state import State, AnalyzerState
from src.tools import data_analyzer
from src.prompts import (
    DRAFT_REPORT_GENERATOR_PROMPT,
    FINAL_REPORT_GENERATOR_PROMPT
)
from config import (
    RENTCAST_API_KEY,
    RENTCAST_URL,
    MAX_RADIUS,
    ARCGIS_USERNAME,
    ARCGIS_PASSWORD,
    ARCGIS_URL,
    ARCGIS_ENRICH_URL,
    OPENAI_MODEL,
    MAX_RETRIES,
    OUTPUT_DIR
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def retry():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(MAX_RETRIES + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        logger.warning(f"[{func.__name__}] Retry {attempt + 1}/{MAX_RETRIES} failed: {e}")
                    else:
                        logger.error(f"[{func.__name__}] Exceeded max retries.", exc_info=True)
                        raise RuntimeError(f"[{func.__name__}] failed after max retries.") from e
        return wrapper
    return decorator


def subject_property_collector(state: State):
    """Collects subject property details from RentCast."""
    logger.info(f"[subject_property_collector] Started subject property collecting.")
    address = state["address"]
    id = address.replace(" ", "-")
    url = f"{RENTCAST_URL}/properties/{id}"
    headers = {"X-Api-Key": RENTCAST_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    subject_property = response.json()
    logger.info(f"[subject_property_collector] Completed subject property collecting.")
    return {"subject_property": [subject_property]}


def sale_listings_collector(state: State):
    """Collects nearby sale listings from RentCast."""
    logger.info(f"[sale_listings_collector] Started sale listings collecting.")
    address = state["address"]
    property_type = state["property_type"]
    url = f"{RENTCAST_URL}/listings/sale"
    headers = {"X-Api-Key": RENTCAST_API_KEY}
    params = {
        "address": address,
        "radius": MAX_RADIUS,
        "propertyType": property_type,
        "limit": 500,
        "offset": 0
    }
    sale_listings = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        sale_listings.extend(data)
        if len(data) < params["limit"]:
            break
        else:
            params["offset"] += 500
    logger.info(f"[sale_listings_collector] Completed sale listings collecting.")
    return {"sale_listings": sale_listings}


def rental_listings_collector(state: State):
    """Collects nearby rental listings from RentCast."""
    logger.info(f"[rental_listings_collector] Started rental listings collecting.")
    address = state["address"]
    property_type = state["property_type"]
    url = f"{RENTCAST_URL}/listings/rental/long-term"
    headers = {"X-Api-Key": RENTCAST_API_KEY}
    params = {
        "address": address,
        "radius": MAX_RADIUS,
        "propertyType": property_type,
        "limit": 500,
        "offset": 0
    }
    rental_listings = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        rental_listings.extend(data)
        if len(data) < params["limit"]:
            break
        else:
            params["offset"] += 500
    logger.info(f"[rental_listings_collector] Completed rental listings collecting.")
    return {"rental_listings": rental_listings}


def demographic_stats_collector(state: State):
    """Collects nearby demographic statistics from ArcGIS."""
    logger.info(f"[demographic_stats_collector] Started demographic statistics collecting.")
    address = state["address"]
    params = {
        "username": ARCGIS_USERNAME,
        "password": ARCGIS_PASSWORD,
        "referer": ARCGIS_URL,
        "f": "json"
    }
    response = requests.post(f"{ARCGIS_URL}/sharing/rest/generateToken", data=params)
    token = response.json().get("token")
    study_areas = [{
        "address": {"text": address}
    }]
    variables = [
        "AGEBASE_CY",
        "POPGRW20CY",
        "POPGRWCYFY",
        "TOTHH_CY",
        "HHGRW20CY",
        "HHGRWCYFY",
        "AVGHHSZ_CY",
        "MEDHINC_CY",
        "MHIGRWCYFY",
        "AVGHINC_CY",
        "PCI_CY",
        "MEDDI_CY",
        "MEDVAL_CY",
        "AVGVAL_CY",
        "EMP_CY",
        "UNEMPRT_CY",
        "DPOP_CY",
        "DPOPWRK_CY",
        "TOTHU_CY",
        "VACANT_CY",
        "OWNER_CY",
        "RENTER_CY",
        "EDUCBASECY",
        "BACHDEG_CY",
        "GRADDEG_CY"
    ]
    params = {
        "token": token,
        "studyAreas": json.dumps(study_areas),
        "analysisVariables": ",".join(variables),
        "f": "json"
    }
    response = requests.post(ARCGIS_ENRICH_URL, data=params)
    demographic_stats = response.json()["results"][0]["value"]["FeatureSet"][0]["features"][0]['attributes']
    logger.info(f"[demographic_stats_collector] Completed demographic statistics collecting.")
    return {"demographic_stats": [demographic_stats]}


def subject_property_processor(state: State):
    """Processes subject property data."""
    logger.info(f"[subject_property_processor] Started subject property processing.")
    subject_property = pd.json_normalize(state["subject_property"])
    subject_property.rename(columns={
        "hoa.fee": "hoaFee", 
        "owner.names": "ownerNames", 
        "owner.type": "ownerType"
    }, inplace=True)
    columns = [
        "addressLine1",
        "addressLine2",
        "bedrooms",
        "bathrooms",
        "squareFootage",
        "lotSize",
        "yearBuilt",
        "hoaFee",
        "lastSaleDate",
        "lastSalePrice",
        "ownerNames",
        "ownerType"
    ]
    subject_property = subject_property.reindex(columns=columns)
    logger.info(f"[subject_property_processor] Completed subject property processing.")
    return {"subject_property": subject_property.to_dict(orient="records")}


def sale_listings_processor(state: State):
    """Processes sale listings and computes summary statistics."""
    logger.info(f"[sale_listings_processor] Started sale listings processing.")
    subject_property = state["subject_property"][0]
    sale_listings = state["sale_listings"]
    sale_listings = pd.json_normalize(sale_listings)
    sale_listings.rename(columns={"hoa.fee": "hoaFee"}, inplace=True)
    sale_listings["pricePerSquareFoot"] = (sale_listings["price"] / sale_listings["squareFootage"]).round(2)
    columns = [
        "addressLine1",
        "addressLine2",
        "bedrooms",
        "bathrooms",
        "squareFootage",
        "lotSize",
        "yearBuilt",
        "hoaFee",
        "price",
        "pricePerSquareFoot",
        "listedDate",
        "lastSeenDate",
        "daysOnMarket"
    ]
    sale_listings = sale_listings.reindex(columns=columns)
    mask = (
        (((sale_listings["bedrooms"] - subject_property["bedrooms"]).abs() <= 1) & ((sale_listings["bathrooms"] - subject_property["bathrooms"]).abs() <= 1)) \
        | sale_listings["squareFootage"].between(subject_property["squareFootage"]*0.80, subject_property["squareFootage"]*1.20, inclusive="both")
    )
    sale_comps = sale_listings.loc[mask]
    sale_listings_stats = pd.DataFrame([{
        "averagePrice": sale_listings["price"].mean(),
        "medianPrice": sale_listings["price"].median(),
        "minPrice": sale_listings["price"].min(),
        "maxPrice": sale_listings["price"].max(),
        "averagePricePerSquareFoot": sale_listings["pricePerSquareFoot"].mean(),
        "medianPricePerSquareFoot": sale_listings["pricePerSquareFoot"].median(),
        "minPricePerSquareFoot": sale_listings["pricePerSquareFoot"].min(),
        "maxPricePerSquareFoot": sale_listings["pricePerSquareFoot"].max(),
        "averageSquareFootage": sale_listings["squareFootage"].mean(),
        "medianSquareFootage": sale_listings["squareFootage"].median(),
        "minSquareFootage": sale_listings["squareFootage"].min(),
        "maxSquareFootage": sale_listings["squareFootage"].max(),
        "averageYearBuilt": sale_listings["yearBuilt"].mean(),
        "medianYearBuilt": sale_listings["yearBuilt"].median(),
        "minYearBuilt": sale_listings["yearBuilt"].min(),
        "maxYearBuilt": sale_listings["yearBuilt"].max(),
        "averageDaysOnMarket": sale_listings["daysOnMarket"].mean(),
        "medianDaysOnMarket": sale_listings["daysOnMarket"].median(),
        "minDaysOnMarket": sale_listings["daysOnMarket"].min(),
        "maxDaysOnMarket": sale_listings["daysOnMarket"].max(),
        "totalListings": len(sale_listings)
    }])
    logger.info(f"[sale_listings_processor] Completed sale listings processing.")
    return {
        "sale_listings": sale_listings.to_dict(orient="records"),
        "sale_comps": sale_comps.to_dict(orient="records"),
        "sale_listings_stats": sale_listings_stats.to_dict(orient="records")
    }


def rental_listings_processor(state: State):
    """Processes rental listings and computes summary statistics."""
    logger.info(f"[rental_listings_processor] Started rental listings processing.")
    subject_property = state["subject_property"][0]
    rental_listings = state["rental_listings"]
    rental_listings = pd.json_normalize(rental_listings)
    rental_listings.rename(columns={"hoa.fee": "hoaFee", "price": "rent"}, inplace=True)
    rental_listings["rentPerSquareFoot"] = (rental_listings["rent"] / rental_listings["squareFootage"]).round(2)
    columns = [
        "addressLine1",
        "addressLine2",
        "bedrooms",
        "bathrooms",
        "squareFootage",
        "lotSize",
        "yearBuilt",
        "hoaFee",
        "rent",
        "rentPerSquareFoot",
        "listedDate",
        "lastSeenDate",
        "daysOnMarket"
    ]
    rental_listings = rental_listings.reindex(columns=columns)
    mask = (
        (((rental_listings["bedrooms"] - subject_property["bedrooms"]).abs() <= 1) & ((rental_listings["bathrooms"] - subject_property["bathrooms"]).abs() <= 1)) \
        | rental_listings["squareFootage"].between(subject_property["squareFootage"]*0.80, subject_property["squareFootage"]*1.20, inclusive="both")
    )
    rental_comps = rental_listings.loc[mask]
    rental_listings_stats = pd.DataFrame([{
        "averageRent": rental_listings["rent"].mean(),
        "medianRent": rental_listings["rent"].median(),
        "minRent": rental_listings["rent"].min(),
        "maxRent": rental_listings["rent"].max(),
        "averageRentPerSquareFoot": rental_listings["rentPerSquareFoot"].mean(),
        "medianRentPerSquareFoot": rental_listings["rentPerSquareFoot"].median(),
        "minRentPerSquareFoot": rental_listings["rentPerSquareFoot"].min(),
        "maxRentPerSquareFoot": rental_listings["rentPerSquareFoot"].max(),
        "averageSquareFootage": rental_listings["squareFootage"].mean(),
        "medianSquareFootage": rental_listings["squareFootage"].median(),
        "minSquareFootage": rental_listings["squareFootage"].min(),
        "maxSquareFootage": rental_listings["squareFootage"].max(),
        "averageYearBuilt": rental_listings["yearBuilt"].mean(),
        "medianYearBuilt": rental_listings["yearBuilt"].median(),
        "minYearBuilt": rental_listings["yearBuilt"].min(),
        "maxYearBuilt": rental_listings["yearBuilt"].max(),
        "averageDaysOnMarket": rental_listings["daysOnMarket"].mean(),
        "medianDaysOnMarket": rental_listings["daysOnMarket"].median(),
        "minDaysOnMarket": rental_listings["daysOnMarket"].min(),
        "maxDaysOnMarket": rental_listings["daysOnMarket"].max(),
        "totalListings": len(rental_listings)
    }])
    logger.info(f"[rental_listings_processor] Completed rental listings processing.")
    return {
        "rental_listings": rental_listings.to_dict(orient="records"),
        "rental_comps": rental_comps.to_dict(orient="records"),
        "rental_listings_stats": rental_listings_stats.to_dict(orient="records")
    }


def demographic_stats_processor(state: State):
    """Processes demographic statistics."""
    logger.info(f"[demographic_stats_processor] Started demographic statistics processing.")
    demographic_stats = state["demographic_stats"]
    demographic_stats = pd.DataFrame(demographic_stats)
    columns = [
        "AGEBASE_CY",
        "POPGRW20CY",
        "POPGRWCYFY",
        "TOTHH_CY",
        "HHGRW20CY",
        "HHGRWCYFY",
        "AVGHHSZ_CY",
        "MEDHINC_CY",
        "MHIGRWCYFY",
        "AVGHINC_CY",
        "PCI_CY",
        "MEDDI_CY",
        "MEDVAL_CY",
        "AVGVAL_CY",
        "EMP_CY",
        "UNEMPRT_CY",
        "DPOP_CY",
        "DPOPWRK_CY",
        "TOTHU_CY",
        "VACANT_CY",
        "OWNER_CY",
        "RENTER_CY",
        "EDUCBASECY",
        "BACHDEG_CY",
        "GRADDEG_CY"
    ]
    demographic_stats = demographic_stats.reindex(columns=columns)
    logger.info(f"[demographic_stats_processor] Completed demographic statistics processing.")
    return {"demographic_stats": demographic_stats.to_dict(orient="records")}


@retry()
def draft_report_generator(state: State):
    """Generates a draft report using the collected datasets."""
    logger.info(f"[draft_report_generator] Started draft report generating.")
    address = state["address"]
    property_type = state["property_type"]
    subject_property = state["subject_property"]
    sale_listings = state["sale_listings"]
    sale_comps = state["sale_comps"]
    sale_listings_stats = state["sale_listings_stats"]
    rental_listings = state["rental_listings"]
    rental_comps = state["rental_comps"]
    rental_listings_stats = state["rental_listings_stats"]
    demographic_stats = state["demographic_stats"]
    llm = ChatOpenAI(model=OPENAI_MODEL, reasoning_effort="high")
    agent = create_react_agent(
        model=llm,
        tools=[data_analyzer],  
        prompt=DRAFT_REPORT_GENERATOR_PROMPT,
        state_schema=AnalyzerState
    )
    response = agent.invoke({
        "messages": "\n".join([
            "Generate a draft report for the following property.",
            f"Address: {address}",
            f"Property Type: {property_type}"
        ]),
        "subject_property": subject_property,
        "sale_listings": sale_listings,
        "sale_comps": sale_comps,
        "sale_listings_stats": sale_listings_stats,
        "rental_listings": rental_listings,
        "rental_comps": rental_comps,
        "rental_listings_stats": rental_listings_stats,
        "demographic_stats": demographic_stats
    }, config={"recursion_limit": 150})
    draft_report = response["messages"][-1].content
    logger.info(f"[draft_report_generator] Completed draft report generating.")
    return {"draft_report": draft_report}


@retry()
def final_report_generator(state: State):
    """Generates a final report based on the draft."""
    logger.info(f"[final_report_generator] Started final report generating.")
    draft_report = state["draft_report"]
    llm = ChatOpenAI(model=OPENAI_MODEL, reasoning_effort="high", verbosity="high")
    messages = [
        ("system", f"{FINAL_REPORT_GENERATOR_PROMPT}"),
        ("human", "\n".join([
            "Generate a final report based on the following draft.",
            f"Draft Report:\n{draft_report}"
        ]))
    ]
    response = llm.invoke(messages)
    final_report = response.content
    logger.info(f"[final_report_generator] Completed final report generating.")
    return {"final_report": final_report}


def pdf_converter(state: State):
    """Converts the final report to a PDF file."""
    logger.info(f"[pdf_converter] Started pdf converting.")
    final_report = state["final_report"]
    pdf = MarkdownPdf(toc_level=3, optimize=True)
    pdf.add_section(Section(final_report, toc=False))
    output_path = f"{OUTPUT_DIR}/final_report_{uuid4().hex[:8]}.pdf"
    pdf.save(output_path)
    logger.info(f"[pdf_converter] Completed pdf converting.")
    return {"output_path": output_path}