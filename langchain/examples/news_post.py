from aeris_langchain.middleware import AerisMiddleware
from dotenv import load_dotenv
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.runnables import RunnableSequence
from langchain_core.runnables.base import RunnableParallel
from langchain_openai import ChatOpenAI

from langchain.prompts import PromptTemplate

load_dotenv()


def main():
    """
    A basic agent which performs a research task to write a blog post about today's top news stories.

    The following environment variables must be set, or in a .env file in the working directory:
    - AERIS_API_KEY: Your Aeris API key.
    - AERIS_PROJECT_ID: The UUID of your Aeris project.
    - OPENAI_API_KEY: Your OpenAI API key.
    - SERPAPI_API_KEY: Your Google Search API key.
    """

    middleware = AerisMiddleware()

    task_name = "Today's Top News Stories"
    task_input = "Write a blog post about today's top news stories"
    task_id = middleware.register_task(name=task_name, task_input=task_input)
    print(f"Registered task with ID: {task_id}")

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    enriched_prompt = middleware.enrich_prompt(
        task_input=task_input, existing_prompt=task_input
    )
    search_tool = SerpAPIWrapper()

    summarization_prompt = PromptTemplate(
        input_variables=["article"],
        template="Summarize the following article:\n\n{article}",
    )
    summarization_chain = summarization_prompt | llm

    blog_post_prompt = PromptTemplate(
        input_variables=["key_points"],
        template="Write a blog post based on the following key points:\n{key_points}",
    )
    blog_post_chain = blog_post_prompt | llm

    news_to_blog_chain = RunnableSequence(
        steps=[
            # Search for news headlines
            search_tool,
            # Summarize articles
            RunnableParallel({"summaries": summarization_chain}),
            # Combine summaries and draft a blog post
            RunnableParallel(
                lambda results: {"key_points": "\n".join(results["summaries"])}
            )
            | blog_post_chain,
        ]
    )

    blog_post = news_to_blog_chain.invoke(enriched_prompt)
    print(blog_post)


if __name__ == "__main__":
    main()
