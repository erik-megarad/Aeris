import os

from colorama import Fore, Style
from dotenv import load_dotenv
from llama_index.core.agent.workflow import (
    AgentInput,
    AgentOutput,
    AgentStream,
    AgentWorkflow,
    FunctionAgent,
    ReActAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

from aeris_llamaindex.client import AerisClient
from aeris_llamaindex.examples.tools.lookup_location import lookup_location
from aeris_llamaindex.examples.tools.lookup_weather import (
    guess_unit_of_measurement,
    lookup_weather,
)
from aeris_llamaindex.examples.tools.search_web import search_web
from aeris_llamaindex.tools import fetch_similar_tasks

load_dotenv()


llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
# reasoning_llm = Replicate(
#    model="deepseek-ai/deepseek-r1", api_key=os.getenv("REPLICATE_API_TOKEN")
# )
reasoning_llm = OpenAI(model="o1-mini", api_key=os.getenv("OPENAI_API_KEY"))


async def record_planning_advice_fn(ctx: Context, advice: str) -> str:
    """Useful for recording advice before planning a task."""
    current_state = await ctx.get("state")
    current_state["advice"] = advice
    await ctx.set("state", current_state)
    return f"Advice recorded: {advice}"


record_planning_advice = FunctionTool.from_defaults(record_planning_advice_fn)


async def record_plan_fn(ctx: Context, plan: str) -> str:
    """Useful for recording a plan for executing a task."""
    current_state = await ctx.get("state")
    current_state["plan"] = plan
    await ctx.set("state", current_state)
    return f"Plan recorded: {plan}"


record_plan = FunctionTool.from_defaults(record_plan_fn)


async def record_output_fn(ctx: Context, script: str) -> str:
    """Useful for recording a the desired output requested by the user."""
    current_state = await ctx.get("state")
    current_state["script"] = script
    await ctx.set("state", current_state)
    return f"Script recorded: {script}"


record_output = FunctionTool.from_defaults(record_output_fn)


preplanning_agent = FunctionAgent(
    name="TaskPrePlanningAgent",
    description="Useful for gathering advice before planning a task.",
    system_prompt=(
        "You are the TaskPrePlanningAgent. You excel at gathering advice before planning a task."
        "Given the execution results of previous tasks that are similar, you can provide advice on how to proceed."
        "Once you have gathered advice, hand off to the TaskPlanningAgent."
    ),
    llm=llm,
    tools=[fetch_similar_tasks, record_planning_advice],
    can_handoff_to=["TaskPlanningAgent"],
)

planning_agent = ReActAgent(
    name="TaskPlanningAgent",
    description="Useful for developing or refining a task execution plan.",
    system_prompt=(
        "You are the TaskPlanningAgent. You excel at taking a human-provided task and developing a plan to execute it, as well as refining that plan based on current execution status."
        "Once you have developed a plan, hand off execution to the TaskExecutionAgent."
    ),
    llm=reasoning_llm,
    tools=[record_plan],
    can_handoff_to=["TaskExecutionAgent"],
)

execution_agent = ReActAgent(
    name="TaskExecutionAgent",
    description="Useful for executing the next step of a task execution plan.",
    system_prompt=(
        "You are the TaskExecutionAgent. You excel determining the next step in a plan and handing it off for execution."
        "If you believe the task to be complete, hand off to the TaskReviewAgent."
        "If you know the next step to execute, hand off to the SubTaskExecutionAgent."
        "If you are unsure how to proceed, hand off to the TaskPlanningAgent."
    ),
    llm=reasoning_llm,
    tools=[],
    can_handoff_to=["TaskPlanningAgent", "SubTaskExecutionAgent", "TaskReviewAgent"],
)

subtask_execution_agent = FunctionAgent(
    name="SubTaskExecutionAgent",
    description="Useful for executing subtasks based on a plan.",
    system_prompt=(
        "You are the SubTaskExecutionAgent. You excel at executing the next subtask based on a plan."
    ),
    llm=llm,
    tools=[
        lookup_location,
        guess_unit_of_measurement,
        lookup_weather,
        search_web,
        record_output,
    ],
    can_handoff_to=["TaskExecutionAgent"],
)

review_agent = ReActAgent(
    name="TaskReviewAgent",
    description="Useful for reviewing the status of a task execution.",
    system_prompt=(
        "You are the TaskReviewAgent. You excel at reviewing the status of a task execution, determining if it is complete, and providing feedback."
    ),
    llm=reasoning_llm,
    tools=[],
    can_handoff_to=["TaskPlanningAgent"],
)

agent_workflow = AgentWorkflow(
    agents=[preplanning_agent, planning_agent, execution_agent, review_agent],
    root_agent="TaskPrePlanningAgent",
    initial_state={
        "advice": "",
        "task": "",
        "plan": [],
        "data": {},
        "task_id": "",
        "script": "",
    },
    state_prompt="Current state: {state}. User message: {msg}",
)

aeris_client = AerisClient()


async def main():
    # task = input("What would you like me to do? ")
    task = "In the form of a two-minute video script give me a weather report for Denver, CO"
    task_id = await aeris_client.register_task(name=task, task_input=task)
    handler = agent_workflow.run(
        user_msg=task,
        state={
            "advice": "",
            "task": task,
            "plan": [],
            "data": {},
            "task_id": task_id,
            "script": "",
        },
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
            print("📥 Input:\n-----")
            print(format_messages(event.input))
            print("-----")
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

    state = await handler.ctx.get("state")
    print(f"Finished script:\n-----\n{state['script']}\n-----")
    breakpoint()
    human_success = input("Is the task complete? (y/n) ").lower() == "y"
    human_feedback = input("What is your feedback on the execution of the task? ")
    await aeris_client.end_task(human_success, human_feedback)


def format_messages(messages: list[ChatMessage]) -> str:
    """Nicely format the chat messages for console output with colors"""
    formatted_messages = []
    for message in messages:
        formatted_message = ""
        if message.role == MessageRole.USER:
            formatted_message += Fore.BLUE + "👤 "
        elif (
            message.role == MessageRole.ASSISTANT
            or message.role == MessageRole.MODEL
            or message.role == MessageRole.CHATBOT
        ):
            formatted_message += Fore.GREEN + "🤖 "
        elif message.role == MessageRole.TOOL:
            formatted_message += Fore.YELLOW + "🔧 "
        elif message.role == MessageRole.SYSTEM:
            formatted_message += Fore.CYAN + "🌐 "
        else:
            formatted_message += Fore.RED + "❓ "

        if message.content:
            formatted_message += message.content
        elif "tool_calls" in message.additional_kwargs:
            formatted_message += f"Tools: {', '.join([call.model_dump_json() for call in message.additional_kwargs['tool_calls']])}"
        else:
            formatted_message += message.model_dump_json()

        formatted_message += Style.RESET_ALL

        formatted_messages.append(formatted_message)

    return "\n".join(formatted_messages)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
