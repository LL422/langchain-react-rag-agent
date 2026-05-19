import os
from utils.logger_handler import logger
from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]

external_data = {}


@tool(description="Retrieve reference materials from the vector store")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


@tool(description="Get the weather for a specified city, returned as a message string")
def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 26°C, humidity 50%, south wind 1 level, AQI 21, very low precipitation probability in the next 6 hours"


@tool(description="Get the current user's city name, returned as a plain string")
def get_user_location() -> str:
    return random.choice(["Shenzhen", "Hefei", "Hangzhou"])


@tool(description="Get the current user's ID, returned as a plain string")
def get_user_id() -> str:
    return random.choice(user_ids)


@tool(description="Get the current month, returned as a plain string in YYYY-MM format")
def get_current_month() -> str:
    return random.choice(month_arr)


def generate_external_data():
    """
    Parses the external data CSV into a nested dict:
    {
        "user_id": {
            "month": {"Feature": xxx, "Efficiency": xxx, ...}
            ...
        },
        ...
    }
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"External data file not found: {external_data_path}")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "Feature": feature,
                    "Efficiency": efficiency,
                    "Consumables": consumables,
                    "Comparison": comparison,
                }


@tool(description="Fetch the usage record for a specified user in a specified month from the external system. Returns a plain string, or an empty string if no record is found.")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return str(external_data[user_id][month])
    except KeyError:
        logger.warning(f"[fetch_external_data] No record found for user {user_id} in {month}")
        return ""


@tool(description="No input, no return value. When called, triggers middleware to dynamically inject context for report generation scenarios, enabling subsequent prompt switching.")
def fill_context_for_report():
    return "fill_context_for_report called"
