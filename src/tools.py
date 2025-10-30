import os
os.environ["MPLBACKEND"] = "Agg"
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM
from pandasai.core.response.chart import ChartResponse

from config import PANDASAI_MODEL


@tool
def data_analyzer(
      query: str, 
      subject_property: Annotated[list[dict], InjectedState("subject_property")],
      sale_listings: Annotated[list[dict], InjectedState("sale_listings")],
      sale_comps: Annotated[list[dict], InjectedState("sale_comps")],
      sale_listings_stats: Annotated[list[dict], InjectedState("sale_listings_stats")],
      rental_listings: Annotated[list[dict], InjectedState("rental_listings")],
      rental_comps: Annotated[list[dict], InjectedState("rental_comps")],
      rental_listings_stats: Annotated[list[dict], InjectedState("rental_listings_stats")],
      demographic_stats: Annotated[list[dict], InjectedState("demographic_stats")],
   ) -> str:
   """
   Performs data analysis tasks based on a natural-language query over injected in-memory DataFrames using PandasAI.

   Args:
      query (str): Natural-language query.

   Returns:
      response (str): One of the following response types:
         - DataFrame Response: Tabular data
         - Number Response: Computed numeric value
         - String Response: Explanation or insight
         - Chart Response: Saved path of the chart image
         - Error Response: JSON-formatted error message
   """
   llm = LiteLLM(model=PANDASAI_MODEL)
   pai.config.set({
      "llm": llm
   })

   dfs = [
      pai.DataFrame(subject_property, _table_name="subject_property"),
      pai.DataFrame(sale_listings, _table_name="sale_listings"),
      pai.DataFrame(sale_comps, _table_name="sale_comps"),
      pai.DataFrame(sale_listings_stats, _table_name="sale_listings_stats"),
      pai.DataFrame(rental_listings, _table_name="rental_listings"),
      pai.DataFrame(rental_comps, _table_name="rental_comps"),
      pai.DataFrame(rental_listings_stats, _table_name="rental_listings_stats"),
      pai.DataFrame(demographic_stats, _table_name="demographic_stats")
   ]

   response = pai.chat(query, *dfs)

   if isinstance(response, ChartResponse):
      file_path = response.value
      response.save(file_path)
      return file_path
   else:
      return str(response.value)