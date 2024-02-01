import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

load_dotenv()

DESCRIPTION_MODEL = os.getenv("DESCRIPTION_MODEL", "gpt-4-vision-preview")

DESCRIPTION_PROMPT = os.getenv(
    "DESCRIPTION_PROMPT",
    "Describe this image. Focus on the cat or cats in the photo. What do they look like? What are they doing? In "
    "what surroundings are they?"
)

TAGS_MODEL = os.getenv("TAGS_MODEL", "gpt-3.5-turbo")

TAGS_PROMPT = os.getenv(
    "TAGS_PROMPT",
    "The following description is about cats and their surroundings. Extract up to five useful tags such as the "
    "number of cats, their color, their actions, and where they are (e.g. pavement, roof, couch). The tags should be "
    "lower case and if multiple words, separated by a '-' (e.g. single-cat). Do not include any bullet points or "
    "numbers in the response, just a comma-separated list of tags. Description:"
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "DEBUG"))
logger = logging.getLogger(__name__)

client = AsyncOpenAI()
app = FastAPI()


@app.get("/{imgid}")
async def get_image(imgid: str):
    async with httpx.AsyncClient() as c:
        response = await c.get(mkurl(imgid))
        if not response.is_success:
            logger.debug(f"{response.status_code} {response.text}")

    return Response(status_code=response.status_code, headers=response.headers, content=response.content)


class DescriptionResponseBody(BaseModel):
    description: str
    imgid: str


@app.get("/{imgid}/description")
async def get_image_description(imgid: str) -> DescriptionResponseBody:
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": DESCRIPTION_PROMPT
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": mkurl(imgid)
                    }
                }
            ]
        }
    ]

    chat_completions = await client.chat.completions.create(messages=messages, model=DESCRIPTION_MODEL, max_tokens=1000)
    description = get_assistant_message(chat_completions, "the assistant is out for lunch")
    return DescriptionResponseBody(description=description, imgid=imgid)


class TagsRequestBody(BaseModel):
    description: str


class TagsResponseBody(BaseModel):
    tags: list[str]
    imgid: str


@app.post("/{imgid}/tags")
async def get_image_tags(imgid: str, body: TagsRequestBody) -> TagsResponseBody:
    messages = [
        {
            "role": "user",
            "content": f"{TAGS_PROMPT} {body.description}"
        }
    ]

    chat_completions = await client.chat.completions.create(messages=messages, model=DESCRIPTION_MODEL, max_tokens=10)
    message = get_assistant_message(chat_completions, "")
    tags = [t.strip() for t in message.split(",")]
    return TagsResponseBody(tags=tags, imgid=str(imgid))


def get_assistant_message(chat_completions: ChatCompletion, default=None):
    for choice in chat_completions.choices:
        if choice.message.role == "assistant":
            return choice.message.content

    return default


IMAGE_URL_TMPL = os.getenv("IMAGE_URL_TMPL")


def mkurl(imgid: str) -> str:
    return IMAGE_URL_TMPL.format(imgid=imgid)
