from openai import OpenAI

from aeris.env import get_setting


def generate_openai_embedding(text: str, model: str = "text-embedding-ada-002") -> list[float]:
    # Ensure the input text is within the token limit for the model
    if not text or not isinstance(text, str):
        raise ValueError("Input text must be a non-empty string.")

    api_key = get_setting("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding
