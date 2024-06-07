from enum import Enum
import os
from typing import List, Dict, override, Optional
import base64
from openai import OpenAI
from openai import OpenAIError
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from openai.lib.streaming import AssistantEventHandler
from openai.types.beta import Thread

# get api key from .env
load_dotenv()
open_ai_key = os.getenv("OPENAI_API_KEY")


class OpenAIModels(Enum):
    GPT_4o = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > {text}", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)


class OpenAIAssistant:
    """
    Calls to Assistants API required a beta HTTP header
    OpenAI-Beta: assistants=v2
    """

    def __init__(self, name: str, instructions: str, tools: List[Dict[str, str]] = None,
                 model=OpenAIModels.GPT_4o.value, thread_id: str = None):
        self.client = OpenAI(api_key=open_ai_key)

        if tools is None:
            tools = [{"type": "code_interpreter"}]

        self.assistant = self.client.beta.assistants.create(name=name, instructions=instructions, tools=tools,
                                                            model=model)
        if not thread_id:
            self.thread = self.client.beta.threads.create()
        else:
            self.thread = self.client.beta.threads.retrieve(thread_id)

        self.instructions = instructions
        self.model = model

    def add_message_to_thread(self, thread: Thread, content: str):
        return self.client.beta.threads.messages.create(thread_id=thread.id, role="user", content=content)

    def get_current_thread(self) -> Thread:
        return self.thread

    def make_new_thread(self) -> Thread:
        self.thread = self.client.beta.threads.create()
        return self.thread

    def run_stream(self):
        """
        Then, we use the `stream` SDK helper
            with the `EventHandler` class to create the Run
            and stream the response.
        """
        event_handler = EventHandler()
        with self.client.beta.threads.runs.stream(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=self.instructions,
                event_handler=event_handler,
        ) as stream:
            stream.until_done()


class OpenAIConnect:
    def __init__(
            self,
            system_prompt="",
            temperature=0.5,
            max_tokens=500,
            model: str = OpenAIModels.GPT_4o.value,
            json_format: str = None,
            timeout=20
    ):
        self.client = OpenAI(api_key=open_ai_key)
        if not json_format:
            json_format = """
            {
                "response":"string"
            }
            """
        self.json_format = json_format

        if not system_prompt:
            system_prompt = f"""
            Please respond in json format: {self.json_format}. 
            """
        else:
            system_prompt += f"\n Please respond in json format: {self.json_format}. "
        self.system_prompt = system_prompt

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        self.timeout = timeout



    def get_response(self, prompt: str, previous_messages: list[str] = None, system_prompt: str = None, image: bytes = None) -> str:
        if not system_prompt:
            system_prompt = self.system_prompt

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # add context if there are previous messages
        if previous_messages:
            for i, message in enumerate(previous_messages):
                # TODO alternate for assistant
                # assuming it begins with user message
                if i % 2 == 0 or i == 0:
                    messages.append({"role": "user", "content": message})
                else:
                    messages.append({"role": "assistant", "content": message})

        # attach latest message
        messages.append({"role": "user", "content": prompt})

        # TODO handle image

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
