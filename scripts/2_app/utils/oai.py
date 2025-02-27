from typing import List

import tiktoken
from decouple import config
from jinja2 import Template

from openai import OpenAI
from openai import OpenAI as Client
from utils_fun import read_sqlite_file

from .logging import log

# OPENAI_API_KEY = read_sqlite_file("data_1.sqlite")


class OAI:
    def __init__(self):
        # self.client = Client(api_key=str(OPENAI_API_KEY))
        # MODEL = config("MODEL")
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))


class OAIEmbedding(OAI):
    def generate(self, text: str) -> List[float]:
        return (
            self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small",
            )
            .data[0]
            .embedding
        )


def count_token(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


class OAIChat(OAI):
    def generate(self, messages: list, **kwargs) -> List[float]:
        # chat api may return message with no content.
        message = (
            self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                **kwargs,
            )
            .choices[0]
            .message
        )
        return getattr(message, "content", "")

    def stream(self, messages: list, **kwargs):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            **kwargs,
        )

        for chunk in response:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            else:
                yield ""


def render_with_token_limit(template: Template, token_limit: int, **kwargs) -> str:
    text = template.render(**kwargs)
    token_count = count_token(text)
    if token_count > token_limit:
        message = f"token count {token_count} exceeds limit {token_limit}"
        log(message)
        raise ValueError(message)
    return text


if __name__ == "__main__":
    print(count_token("hello world, this is impressive"))
