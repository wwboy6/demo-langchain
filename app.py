from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
from langchain import hub
import requests

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = FastAPI(title="Claude Agent API with Weather Tool")


class Message(BaseModel):
    content: str

@tool
def get_current_weather(location: str) -> str:
    """Get the current weather for a given location (city name)."""
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": location, "count": 1}
    geo_response = requests.get(geo_url, params=geo_params)
    if geo_response.status_code != 200 or not geo_response.json().get("results"):
        return f"Could not find location: {location}"
    
    result = geo_response.json()["results"][0]
    latitude = result["latitude"]
    longitude = result["longitude"]
    
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code"
    }
    weather_response = requests.get(weather_url, params=weather_params)
    if weather_response.status_code != 200:
        return "Error fetching weather data"
    
    current = weather_response.json()["current"]
    
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        51: "Light drizzle",
        61: "Slight rain",
        71: "Slight snow",
    }
    code = current.get("weather_code", 0)
    description = weather_codes.get(code, "Unknown")
    
    return (
        f"Current weather in {location}:\n"
        f"Temperature: {current['temperature_2m']}°C\n"
        f"Humidity: {current['relative_humidity_2m']}%\n"
        f"Precipitation: {current['precipitation']} mm\n"
        f"Condition: {description}"
    )

llm = ChatOpenAI(
    model="anthropic/claude-3-sonnet-20240229",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    temperature=0,
)

# Tools list
tools = [get_current_weather]

prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_openai_tools_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

@app.post("/chat")
async def chat(message: Message):
    try:
        response = agent_executor.invoke({"input": message.content})
        return {"response": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
