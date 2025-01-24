from langchain_core.callbacks.base import BaseCallbackHandler

class AerisCallbackHandler(BaseCallbackHandler):
    def __init__(self, middleware):
        self.middleware = middleware
        
    def on_agent_action(self, action, *, run_id, parent_run_id = None, **kwargs):
        breakpoint()
        self.middleware.log_event(
                task_id=self.task_id,
                event_type="Agent Action",
                event_data={"result": "test"},
            )
        
    def on_llm_end(self, response, *, run_id, parent_run_id = None, **kwargs):
        breakpoint()
        self.middleware.log_event(
                task_id=self.task_id,
                event_type="LLM Response",
                event_data={"result": response.model_dump_json()},
            )
        
