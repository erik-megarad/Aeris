from aeris_langchain.middleware import AerisMiddleware
from dotenv import load_dotenv
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from langchain_core.globals import set_debug
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
    middleware.register_task(name=task_name, task_input=task_input)

    set_debug(True)
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Wrap SerpAPIWrapper as a RunnableLambda
    search_tool = RunnableLambda(lambda query: SerpAPIWrapper().run(query))

    summarization_prompt = PromptTemplate(
        input_variables=["article"],
        template="Summarize the following article:\n\n{article}",
    )
    summarization_chain = summarization_prompt | llm

    blog_post_prompt = PromptTemplate(
        input_variables=["key_points"],
        template="Write a blog post based on the following key points:\n{key_points}",
    )
    blog_post_chain = blog_post_prompt
    # Define the complete workflow using the | operator
    news_to_blog_chain = (
        middleware.prompt_enrichment_runnable() |
        search_tool
        | RunnableLambda(
            lambda articles: [
                summarization_chain.invoke({"article": article}) for article in articles
            ]
        )
        | RunnableLambda(lambda summaries: {"key_points": "\n".join(summaries)})
        | blog_post_chain
    )

    # Run the workflow
    blog_post = news_to_blog_chain.invoke(task_input, config=middleware.config())
    print(blog_post)


if __name__ == "__main__":
    main()
