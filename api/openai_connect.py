from enum import Enum
import os
from openai import OpenAI
from openai import OpenAIError
from bs4 import BeautifulSoup
import requests

from api.models import Food

# get api key from .env
open_ai_key = os.getenv("OPENAI_API_KEY")


class OpenAIModels(Enum):
    GPT_4o = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"


class OpenAIConnect:
    def __init__(
            self,
            system_prompt="",
            temperature=0.5,
            max_tokens=500,
            model: str = OpenAIModels.GPT_4o.value,
            json_object=True,
            json_format: str = None,
            timeout=20
    ):
        self.client = OpenAI()
        self.client.api_key = open_ai_key
        if not json_format:
            json_format = """
            {
                "response":"string"
            }
            """
        self.json_format = json_format
        self.properties: list[str] = Food.all_properties()

        if not system_prompt:
            system_prompt = f"""
            You are a nutritionist who is helping a client track their food intake.
            You are an expert at looking at a photo or description of a meal and determining the nutritional content.
            Please respond in json format: {self.json_format}. 
            Include the following information: {self.properties}
            """
        # print(self.properties)
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        self.json_object = json_object
        self.timeout = timeout

    def get_response(self, prompt: str, system_prompt: str = None) -> str or None:
        if not system_prompt:
            system_prompt = self.system_prompt

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                timeout=self.timeout
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            raise ValueError("Error in OpenAIConnect.get_response: ", e)

    @staticmethod
    def get_recipe_details(url: str) -> str or None:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # get text from all paragraphs
        text = soup.find_all("p")
        text = [t.get_text() for t in text]
        text = " ".join(text)

        return text

    def summarize_recipe_content(self, text: str) -> str or None:
        prompt = """
        Please summarize just the relevant recipe information from the text below. 
        Turn it into one paragraph of information you can use for a recipe database.
        \n
        """
        prompt += text

        return self.get_response(prompt)
