import asyncio
import json
import websockets

AGENT_EMOJIS = {
    "fetch_pr":      "📥",
    "security":      "🔒",
    "logic":         "🧠",
    "test_coverage": "🧪",
    "documentation": "📝",
    "synthesis":     "📋",
}

async def stream_review():
    uri = "ws://localhost:8000/review/stream"
    print(f"Connecting to {uri}...\n")

    async with websockets.connect(uri) as ws:
        # Send the PR URL
        await ws.send(json.dumps({
            "pr_url": "https://github.com/fastapi/fastapi/pull/15508"
        }))

        print("Streaming agent progress:\n")

        async for message in ws:
            event = json.loads(message)
            event_type = event.get("type")
            agent      = event.get("agent", "")
            msg        = event.get("message", "")
            emoji      = AGENT_EMOJIS.get(agent, "⚙️")

            if event_type == "start":
                print(f"🚀 {msg}\n")

            elif event_type == "agent_start":
                print(f"  {emoji} [{agent}] {msg}")

            elif event_type == "agent_done":
                data = event.get("data", {})
                print(f"  {emoji} [{agent}] ✅ {msg}  {data}\n")

            elif event_type == "complete":
                data = event.get("data", {})
                print(f"\n{'=' * 60}")
                print(f"  REVIEW COMPLETE")
                print(f"{'=' * 60}")
                print(f"  Score:          {data.get('overall_score')}/100")
                print(f"  Recommendation: {data.get('recommendation')}")
                print(f"  Summary:        {data.get('summary')}")
                print(f"\n  Top suggestions:")
                for i, s in enumerate(data.get("top_suggestions", []), 1):
                    print(f"    {i}. {s}")
                print(f"{'=' * 60}")
                break

            elif event_type == "error":
                print(f"  ❌ Error: {msg}")
                break

asyncio.run(stream_review())