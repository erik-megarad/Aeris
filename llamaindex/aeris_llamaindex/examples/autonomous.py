import os

from dotenv import load_dotenv
from llama_index.core.agent.workflow import (
    AgentInput,
    AgentOutput,
    AgentStream,
    AgentWorkflow,
    FunctionAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.llms.openai import OpenAI

from aeris_llamaindex.client import AerisClient
from aeris_llamaindex.examples.tools.lookup_location import lookup_location
from aeris_llamaindex.examples.tools.lookup_weather import (
    guess_unit_of_measurement,
    lookup_weather,
)
from aeris_llamaindex.examples.tools.search_web import search_web

load_dotenv()


llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

planning_agent = FunctionAgent(
    name="TaskPlanningAgent",
    description="Useful for developing or refining a task execution plan.",
    system_prompt=(
        "You are the TaskPlanningAgent. You excel at taking a human-provided task and developing a plan to execute it."
    ),
    llm=llm,
    tools=[],
)

execution_agent = FunctionAgent(
    name="SubTaskExecutionAgent",
    description="Useful for executing subtasks based on a plan.",
    system_prompt=(
        "You are the SubTaskExecutionAgent. You excel at executing subtasks based on a plan."
    ),
    llm=llm,
    tools=[lookup_location, guess_unit_of_measurement, lookup_weather, search_web],  # type: ignore
)

review_agent = FunctionAgent(
    name="TaskReviewAgent",
    description="Useful for reviewing the status of a task execution.",
    system_prompt=(
        "You are the TaskReviewAgent. You excel at reviewing the status of a task execution, determining if it is complete, and providing feedback."
    ),
    llm=llm,
    tools=[],
    can_handoff_to=["TaskPlanningAgent"],
)

agent_workflow = AgentWorkflow(
    agents=[planning_agent, execution_agent],
    root_agent="TaskPlanningAgent",
    initial_state={"task": "", "plan": [], "data": {}},
    state_prompt="Current state: {state}. User message: {msg}",
)
aeris_client = AerisClient()


async def main():
    task = input("What would you like me to do? ")
    await aeris_client.register_task(name=task, task_input=task)
    handler = agent_workflow.run(
        user_msg=task,
        state={"task": task, "plan": [], "data": {}},
    )

    current_agent = None
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 Agent: {current_agent}")
            print(f"{'='*50}\n")

        if isinstance(event, AgentStream):
            if event.delta:
                print(event.delta, end="", flush=True)
            continue

        await aeris_client.log_llama_event(event)
        if isinstance(event, AgentInput):
            print("📥 Input:", event.input)
        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    "🛠️  Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 Tool Result ({event.tool_name}):")
            print(f"  Arguments: {event.tool_kwargs}")
            print(f"  Output: {event.tool_output}")
        elif isinstance(event, ToolCall):
            print(f"🔨 Calling Tool: {event.tool_name}")
            print(f"  With arguments: {event.tool_kwargs}")

    human_success = input("Is the task complete? (y/n) ").lower() == "y"
    human_feedback = input("What is your feedback on the execution of the task? ")
    await aeris_client.end_task(human_success, human_feedback)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
