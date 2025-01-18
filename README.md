# Aeris: Agent Experience Repository for Intelligent Systems

Aeris is an open-source tool for capturing, storing, and querying AI agent execution data. It’s designed to work across different frameworks, so your agents can learn from past executions by looking back at what they’ve done before—what tasks they’ve tackled, tools they’ve used, and how it all turned out. Collectively, agents will be able to eliminate the expensive trial-and-error process by learning from other agents that have completed similar tasks.

## Current Status

I'm just getting started! Most of what’s in this README isn’t built yet, but it’s on the roadmap. Contributions, ideas, and feedback are totally welcome— I intend for this to eventually be a community project.

## Features

Here’s what I'm working towards:

- **Works with Any Framework**: Compatible with AI agent frameworks like Microsoft Autogen, LlamaIndex Workflows, LangChain, agent-protocol, and others.
- **Detailed Task Logs**: Keeps track of everything—inputs, outputs, tools used, and metadata—so your agents know what’s worked (and what hasn’t).
- **Semantic Search**: Store and search tasks using vector embeddings using `pgvector`. Note: Other vector databases may be supported in the future. Currently `pgvector` is good enough and doesn't require an additional dependency.
- **Powerful Queries**: Use GraphQL to dig into your data with flexible, graph-based queries.
- **Tool Database**: Track the effectiveness of tools to ensure the right tool is being used for the task.

## Background Research

Aeris builds on some cool ideas that aren't mine. Here are a few highlights:

- **Experience Replay**: Techniques in reinforcement learning that enable agents to recall and learn from prior experiences. ([arxiv.org](https://arxiv.org/abs/2007.06700))

- **Knowledge Graphs**: Modern AI applications often leverage knowledge graphs to model complex relationships. Studies integrating deep learning with knowledge graphs demonstrate improvements in reasoning and execution. ([ieeexplore.ieee.org](https://ieeexplore.ieee.org/document/10716359))

- **Case-Based Reasoning**: Drawing from principles of solving new problems by referencing past cases, which enhances event prediction using case-based reasoning with knowledge graphs. ([arxiv.org](https://arxiv.org/abs/2309.12423))

## Getting Started

Here’s how to get up and running:

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/aeris.git
   cd aeris
   ```

2. Install the dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Set up the database:
   ```bash
   poetry run python scripts/init_db.py
   ```
   (TODO: DB instance setup / dockerization)

4. Fire up the development server:
   ```bash
   poetry run uvicorn aeris.main:app --reload
   ```

5. Open [http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql) to play around with the GraphQL API.

### Example Query

**Create a Task**
```graphql
mutation {
  createTask(
    name: "News Generator",
    input: "Write a blog post about the latest news stories",
    output: null,
    tools: ["tool1", "tool2"],
  ) {
    id
    name
  }
}
```

**Search for Similar Tasks**
```graphql
query {
  searchTasks(input: "Write a blog post about today's news", limit: 5) {
    id
    name
    tools
  }
}
```

## Architecture

Aeris is built with:

- **FastAPI**: A modern, async-first web framework for Python.
- **Ariadne**: Schema-first GraphQL implementation.
- **PostgreSQL + pgvector**: Robust relational database with vector similarity search capabilities. Note: Other vector databases may be supported in the future. Currently `pgvector` is good enough and doesn't require an additional dependency.
- **Inngest**: Event-driven task orchestration.

## Contributing

Want to help out? Here’s how to get started:

1. Fork the repo and create a new branch.
2. Make your changes (keeping things clean and consistent).
3. Submit a pull request with a note about what you’ve added.

Before submitting, make sure your code is good to go:
```bash
poetry run mypy
poetry run ruff check .
poetry run pytest
```

## License

Aeris is open source and licensed under the MIT License. Check out the [LICENSE](LICENSE) file for more info.

