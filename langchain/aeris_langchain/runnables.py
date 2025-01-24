from typing import TYPE_CHECKING, Any, Dict, Optional

from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Input 
from langchain_core.runnables.config import  RunnableConfig

if TYPE_CHECKING:
    from aeris_langchain.middleware import AerisMiddleware


class EnrichPromptRunnable(Runnable):
    """
    A Runnable that enriches prompts by fetching and integrating context from similar tasks.
    """

    def __init__(self, middleware: "AerisMiddleware"):
        self.middleware = middleware

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> str:
        breakpoint()
        return self.middleware.enrich_prompt(
            task_input=str(input), existing_prompt=str(input)
        )
