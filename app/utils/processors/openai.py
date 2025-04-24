import openai
import environ
import logging

from typing import List, Dict
from openai import OpenAI

from app.models import OpenaiSettings, Log

env = environ.Env()
env.read_env(env.str("ENV_PATH", ".env"))

logger = logging.getLogger(__name__)

client = OpenAI(api_key=env("OPENAI_API_KEY"))

def chatgpt(
    messages: List[Dict[str, str]],
) -> Dict[str, str]:
    settings = OpenaiSettings.objects.first()
    if not settings:
        logger.error("OpenAI settings not found.")
        return {"status": "Error", "response": "No OpenAI settings found."}

    try:
        response = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            temperature=float(settings.temperature),
        )
    except Exception as e:
        logger.error(f"Can't get a response from ChatGPT: {e}")
        result = {"status": "Error", "response": "No Response", "message": str(e)}
    else:
        try:
            message = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Can't get message from ChatGPT response: {e}")
            result = {"status": "Error", "response": str(response), "message": str(e)}
        else:
            result = {
                "status": "Success",
                "response": response.model_dump(),
                "message": message,
            }

    Log.objects.create(
        model=settings.model,
        temperature=settings.temperature,
        max_retries=settings.max_retries,
        messages=messages,
        result=result,
        is_successful=(result["status"] == "Success"),
    )
    return result
