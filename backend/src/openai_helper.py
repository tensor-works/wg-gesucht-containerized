# in src folder
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_KEY"))


class OpenAIChatHelper:
    """Uses the OpenAI's API and stores previous messages to allow ChatGPT like chats."""

    def __init__(
        self,
        api_key: str,
        primer_prompt: str = "You are an AI assistant",
        model: Optional[str] = "gpt-3.5-turbo",
        temperature: Optional[float] = 0.75,
        max_tokens: Optional[int] = 1000,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # set primer. According to OpenAI it does not always pay attention to system messages,
        # so duplicate as user messages.
        self.messages = [
            {"role": "system", "content": primer_prompt},
            {"role": "user", "content": f"{primer_prompt} Do you understand?"},
            {"role": "assistant", "content": "Yes I understand."},
        ]

    def generate_chat_completion(self):
        """Wrapper around the ChatCompletion class of openai.
        Provides less flexibility than using the endpoint itself."""

        return client.chat.completions.create(model=self.model,
        messages=self.messages,
        temperature=self.temperature,
        max_tokens=self.max_tokens)

    def continue_chat(self, user_prompt):
        self.messages.append(
            {"role": "user", "content": user_prompt},
        )

        chat = self.generate_chat_completion()
        # print(chat)
        reply = chat.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def chat(self):
        """Open loop to begin chatting and add previous message to messages to keep context."""

        while True:
            message = input("User: ")
            if message:
                # saves user message to context.
                self.messages.append(
                    {"role": "user", "content": message},
                )

                chat = self.generate_chat_completion()
                reply = chat.choices[0].message.content

            print(f"ChatGPT: {reply}")
            # saves gpt message to context.
            self.messages.append({"role": "assistant", "content": reply})


class OpenAIHelper:
    def __init__(self, api_key: str):
        ...

    def models(self):
        return client.models.list()

    def retrieve_model(self, model: str):
        return client.models.retrieve(model)

    def generate(
        self, prompt, model="gpt-3.5-turbo", temperature=0.75, max_tokens=1000
    ):
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat.completions.create(model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens)
        response = resp.choices[0].message.content
        return response
