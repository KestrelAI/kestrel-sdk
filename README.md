# Kestrel SDK

Python SDK for [Kestrel](https://usekestrel.ai) — AI Agents for Cloud Operations.

Build, deploy, and manage workflows programmatically with a typed, fluent API.

## Installation

```bash
pip install kestrel-sdk
```

## Quick Start

```python
from kestrel import KestrelClient
from kestrel.workflows import Workflow, Trigger, Action

client = KestrelClient(api_key="kestrel_sk_...")

wf = (
    Workflow("Pod Crash RCA + Jira")
    .description("Run RCA on pod crash, create Jira ticket")
    .trigger(
        Trigger.k8s_pod_status()
        .reasons("CrashLoopBackOff")
        .namespace("production")
    )
    .cooldown(hours=24)
    .then(Action.kestrel_trigger_rca().label("Run RCA"))
    .then(Action.jira_create_ticket()
        .project("KAN")
        .title("{{incident.title}}")
        .priority("High")
    )
)

created = client.workflows.deploy(wf, activate=True)
print(f"Deployed: {created.id}")
```

## Async Support

```python
from kestrel import AsyncKestrelClient

async with AsyncKestrelClient(api_key="kestrel_sk_...") as client:
    workflows = await client.workflows.list()
    execution = await client.workflows.test(workflows[0].id)
    result = await client.executions.wait(execution.id)
    print(f"Result: {result.status}")
```

## Authentication

Create an API key in the Kestrel platform under **Workflows > API Keys**.

```python
# API key (recommended)
client = KestrelClient(api_key="kestrel_sk_...")

# From CLI login
client = KestrelClient.from_config()

# Async
client = AsyncKestrelClient(api_key="kestrel_sk_...")
```

## Documentation

Full SDK documentation: [docs.usekestrel.ai/workflows/sdk](https://docs.usekestrel.ai/workflows/sdk)

## License

Apache 2.0
