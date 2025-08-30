import re

from openai import OpenAI
from config import load_config
from prompts import (
    SUMMARY_SYSTEM_PROMPT,
    SPELLING_CORRECTION_SYSTEM_PROMPT,
    SPELLING_CORRECTION_USER_PROMPT,
    GENERAL_SUMMARY_SYSTEM_PROMPT,
    GENERAL_SUMMARY_USER_PROMPT
)

# Load configuration and initialize client
config = load_config()
client = OpenAI(base_url=config['llm_endpoint'], api_key=config['llm_api_key'])


def call_llm(message, system_prompt=None, schema=None):
    """Call the local LLM."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        if schema is not None:
            response = client.chat.completions.create(
                model=config['llm_model'],
                messages=messages,
                temperature=0.7,
                schema=schema
            )
        else:
            response = client.chat.completions.create(
                model=config['llm_model'],
                messages=messages,
                temperature=0.7
            )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error al llamar al LLM: {e}")
        return None


def generate_summary_with_instruction(note_name, content="", user_instruction=""):
    """Generate a concise conceptual summary with specific user instructions."""
    base_prompt = f"Genera una descripción extremadamente concisa y factual para: {note_name}"

    if content.strip() and len(content) > 50:
        base_prompt += f". Contexto: {content[:300]}"

    if user_instruction.strip():
        base_prompt += f". Instrucción adicional: {user_instruction}"

    message = f"{base_prompt}. Descripción concisa:"

    response = call_llm(message, SUMMARY_SYSTEM_PROMPT)

    # Clean response
    clean_response = response.replace('\n', ' ').strip()
    clean_response = re.sub(r'\s+', ' ', clean_response)

    # If response is too long, ask for a shorter version
    words = clean_response.split()
    if len(words) > 20:
        short_message = f"La siguiente descripción es demasiado larga. Acórtala a máximo 15 palabras: {clean_response}. Descripción corta:"
        short_response = call_llm(short_message, SUMMARY_SYSTEM_PROMPT)
        clean_response = short_response.replace('\n', ' ').strip()
        clean_response = re.sub(r'\s+', ' ', clean_response)

    return clean_response


def correct_spelling(text):
    """Correct spelling and grammar without changing substantial content."""
    message = SPELLING_CORRECTION_USER_PROMPT.format(text=text)
    return call_llm(message, SPELLING_CORRECTION_SYSTEM_PROMPT)


def generate_summary(narrative):
    """Generate a concise summary of the narrative."""
    message = GENERAL_SUMMARY_USER_PROMPT.format(narrative=narrative)
    return call_llm(message, GENERAL_SUMMARY_SYSTEM_PROMPT)
