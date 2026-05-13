import os
from dotenv import load_dotenv

load_dotenv()

print("Checking setup...\n")

checks = {
    "OpenAI API key": os.getenv("OPENAI_API_KEY"),
    "GitHub token": os.getenv("GITHUB_TOKEN"),
    "LangSmith key": os.getenv("LANGCHAIN_API_KEY"),
}

all_good = True
for name, value in checks.items():
    if value and len(value) > 10:
        print(f"  ✅  {name} found")
    else:
        print(f"  ❌  {name} MISSING — check your .env file")
        all_good = False

print()

# Test OpenAI connection
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Reply with just: Setup successful"}],
        max_tokens=10
    )
    print(f"  ✅  OpenAI connection: {response.choices[0].message.content}")
except Exception as e:
    print(f"  ❌  OpenAI connection failed: {e}")
    all_good = False

# Test GitHub connection
try:
    from github import Github
    g = Github(os.getenv("GITHUB_TOKEN"))
    user = g.get_user("torvalds")
    print(f"  ✅  GitHub connection: fetched user '{user.login}' successfully")
except Exception as e:
    print(f"  ❌  GitHub connection failed: {e}")
    all_good = False

# Test LangGraph import
try:
    from langgraph.graph import StateGraph
    print(f"  ✅  LangGraph imported successfully")
except Exception as e:
    print(f"  ❌  LangGraph import failed: {e}")
    all_good = False


print()
if all_good:
    print("🎉  All checks passed — you're ready for Phase 2!")
else:
    print("⚠️   Fix the items above before continuing.")