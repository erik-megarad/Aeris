import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send
from newsapi import NewsApiClient
from typing_extensions import TypedDict

load_dotenv()


class Article(TypedDict):
    title: str
    content: str
    research: str | None


def add_articles(left: list[Article], right: list[Article]) -> list[Article]:
    return left + right


class State(TypedDict):
    messages: Annotated[list, add_messages]
    articles: Annotated[list[Article], add_articles]


graph = StateGraph(State)


class NewsApiBaseTool:
    def __init__(self):
        api_key = os.getenv("NEWSAPI_API_KEY")
        self.client = NewsApiClient(api_key=api_key)


class TopHeadlinesTool(NewsApiBaseTool):
    def __call__(self, state: State) -> dict[str, list[Article]]:
        """Fetch top 3 news headlines from newsapi.org"""
        results = self.client.get_top_headlines(country="us")
        articles = [
            Article(title=article["title"], content=article["content"], research=None)
            for article in results["articles"][:3]
        ]
        return {"articles": articles}


class ResearchArticleTool:
    """Tool to take a single news story, gather more sources, and collate the text into one string"""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    async def __call__(self, article: Article) -> dict[str, list[Article]]:
        """Research the article and generate a summary"""
        response = await self.llm.ainvoke(
            [
                HumanMessage(
                    f"""Provide additional factual context for this news article titled: {article["title"]}.
The article's content is below, however it is truncated. Please provide additional context and information.

{article["content"]}"""
                )
            ]
        )
        article["research"] = response.content
        return {"articles": [article]}


def perform_research(state: State):
    return [Send("research_article", a) for a in state["articles"]]


class BlogSummaryGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    async def __call__(self, state: State) -> str:
        """Generate blog post summary from news items"""
        # Today's date in the format of "Tuesday, 1st January 2022"
        today_date = datetime.now().strftime("%A, %d %B %Y")

        article_collation = "\n\n".join(
            f"""# Article #{i+1}: {article["title"]}\n\nTruncated Content: {article["content"]}\n\nAdditional Research: {article["research"]}\n\n"""
            for i, article in enumerate(state["articles"])
        )

        summary_input = f"""Summarize these 3 news stories in a blog post which expounds upon the themes and draws connections between the stories where reasonable. The blog post should be written in a conversational tone and should be engaging to the reader. The blog post should be dated with today's date: {today_date}.
        
{article_collation}"""
        response = await self.llm.ainvoke([HumanMessage(summary_input)])
        return response.content


# Configure the graph
graph.add_node("get_top_headlines", TopHeadlinesTool())
graph.add_node("research_article", ResearchArticleTool())
graph.add_node("generate_blog_summary", BlogSummaryGenerator())

# Connect nodes and set entry point
graph.add_conditional_edges("get_top_headlines", perform_research, ["research_article"])
graph.add_edge("research_article", "generate_blog_summary")
graph.set_entry_point("get_top_headlines")
graph.set_finish_point("generate_blog_summary")

# Compile the graph
app = graph.compile()


async def stream_graph_updates():
    async for event in app.astream(
        {
            "messages": [],
            "articles": [],
        }
    ):
        for value in event.values():
            print("----")
            breakpoint()
            print(f"Articles: {value.get('articles', 'No articles')}")
            print(f"Messages: {value.get('messages', 'No messages')}")


def main() -> None:
    import asyncio

    asyncio.run(stream_graph_updates())


if __name__ == "__main__":
    main()
