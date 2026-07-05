# Kestrel SDK

Python SDK for [Kestrel](https://usekestrel.ai) — AI Agents for Cloud Operations.

Build, deploy, and manage workflows programmatically with a typed, fluent API.

## Installation

```bash
pip install kestrel-workflows
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

## Integrations

Connect, test, and disconnect Kestrel integrations programmatically.
API keys need the `integrations:read` / `integrations:manage` scopes.

```python
# See every integration and its connection status
for status in client.integrations.list():
    print(status.id, status.connected)

# Inspect credential requirements per integration
for spec in client.integrations.specs():
    print(spec.key, spec.kind, [f.name for f in spec.fields])

# Token integrations take credential kwargs
client.integrations.connect("cloudflare", api_token="...", account_id="...")
client.integrations.connect("pagerduty", api_token="...", webhook_secret="...")

# Knowledge sources
client.integrations.connect(
    "confluence",
    base_url="https://acme.atlassian.net",
    api_key="me@acme.com",   # Atlassian account email
    api_token="...",
)

# OAuth integrations return a URL to open in the browser
url = client.integrations.connect("github")

# Verify and clean up
client.integrations.test("cloudflare")
client.integrations.disconnect("cloudflare")
```

Kubernetes, AWS, and OCI use multi-step flows — connect those with the
Kestrel CLI (`kestrel integrations connect <name> --help`).

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
