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
    """
        This processor provides functionality to interact with OpenAI's ChatGPT API.

        Functions:
            chatgpt(messages: List[Dict[str, str]]) -> Dict[str, str]:
                Sends a list of messages to OpenAI's ChatGPT API and returns the response.

        Dependencies:
            - Requires OpenAI API key to be set in the environment variables.
            - Relies on the OpenaiSettings model for configuration (e.g., model, temperature).
            - Logs interactions and results in the Log model.

        Usage:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the weather today?"}
            ]
            response = chatgpt(messages)
            print(response)
    """

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
