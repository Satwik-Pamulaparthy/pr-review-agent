import os
import sys
import json
import asyncio
from typing import AsyncGenerator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="PR Review Agent",
    description="Multi-agent code review powered by LangGraph + GPT-4o",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    pr_url: str


class ReviewResponse(BaseModel):
    pr_title: str
    pr_author: str
    repo: str
    overall_score: int
    recommendation: str
    summary: str
    security_findings: list
    logic_findings: list
    test_coverage_score: int
    documentation_score: int
    top_suggestions: list
    estimated_review_time_minutes: int
    errors: list


# ── REST endpoint ─────────────────────────────────────────────────────────────

@app.post("/review", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest):
    from graph.workflow import review_graph
    from graph.state import ReviewState

    if "github.com" not in request.pr_url or "/pull/" not in request.pr_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid PR URL. Expected format: https://github.com/owner/repo/pull/123"
        )

    state = ReviewState(pr_url=request.pr_url)

    try:
        final_state = await asyncio.get_event_loop().run_in_executor(
            None, review_graph.invoke, state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    pr     = final_state.get("parsed_pr")
    review = final_state.get("final_review")

    if not pr or not review:
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline failed. Errors: {final_state.get('errors')}"
        )

    return ReviewResponse(
        pr_title=pr.title,
        pr_author=pr.author,
        repo=pr.repo_name,
        overall_score=review.overall_score,
        recommendation=review.recommendation,
        summary=review.summary,
        security_findings=[f.model_dump() for f in final_state.get("security_findings", [])],
        logic_findings=[f.model_dump() for f in final_state.get("logic_findings", [])],
        test_coverage_score=final_state.get("test_coverage").coverage_score if final_state.get("test_coverage") else 0,
        documentation_score=final_state.get("documentation").score if final_state.get("documentation") else 0,
        top_suggestions=review.top_suggestions,
        estimated_review_time_minutes=review.estimated_review_time_minutes,
        errors=final_state.get("errors", []),
    )


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/review/stream")
async def review_pr_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        data   = await websocket.receive_json()
        pr_url = data.get("pr_url", "")

        if "github.com" not in pr_url or "/pull/" not in pr_url:
            await websocket.send_json({"type": "error", "message": "Invalid PR URL"})
            await websocket.close()
            return

        await websocket.send_json({
            "type": "start",
            "message": f"Starting review for: {pr_url}"
        })

        loop = asyncio.get_event_loop()

        async def run_with_progress():
            from graph.state import ReviewState
            from agents.security import run_security_agent
            from agents.logic import run_logic_agent
            from agents.test_coverage import run_test_coverage_agent
            from agents.documentation import run_documentation_agent
            from agents.synthesis import run_synthesis_agent

            state = ReviewState(pr_url=pr_url)

            # Step 1 — Fetch PR
            await websocket.send_json({
                "type": "agent_start",
                "agent": "fetch_pr",
                "message": "Fetching PR from GitHub..."
            })
            state = await loop.run_in_executor(None, lambda: _fetch_pr_step(state, pr_url))
            if state.parsed_pr is None:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to fetch PR: {state.errors}"
                })
                return

            await websocket.send_json({
                "type": "agent_done",
                "agent": "fetch_pr",
                "message": f"Fetched PR #{state.parsed_pr.pr_number}: {state.parsed_pr.title}",
                "data": {
                    "title":     state.parsed_pr.title,
                    "author":    state.parsed_pr.author,
                    "files":     state.parsed_pr.total_files_changed,
                    "additions": state.parsed_pr.total_additions,
                    "deletions": state.parsed_pr.total_deletions,
                }
            })

            # Step 2 — Security
            await websocket.send_json({"type": "agent_start", "agent": "security", "message": "Running security audit..."})
            state = await loop.run_in_executor(None, run_security_agent, state)
            await websocket.send_json({
                "type": "agent_done", "agent": "security",
                "message": f"Found {len(state.security_findings)} security issue(s)",
                "data": {"count": len(state.security_findings)}
            })

            # Step 3 — Logic
            await websocket.send_json({"type": "agent_start", "agent": "logic", "message": "Reviewing logic and correctness..."})
            state = await loop.run_in_executor(None, run_logic_agent, state)
            await websocket.send_json({
                "type": "agent_done", "agent": "logic",
                "message": f"Found {len(state.logic_findings)} logic issue(s)",
                "data": {"count": len(state.logic_findings)}
            })

            # Step 4 — Test coverage
            await websocket.send_json({"type": "agent_start", "agent": "test_coverage", "message": "Analyzing test coverage..."})
            state = await loop.run_in_executor(None, run_test_coverage_agent, state)
            await websocket.send_json({
                "type": "agent_done", "agent": "test_coverage",
                "message": f"Coverage score: {state.test_coverage.coverage_score}/100",
                "data": {"score": state.test_coverage.coverage_score if state.test_coverage else 0}
            })

            # Step 5 — Documentation
            await websocket.send_json({"type": "agent_start", "agent": "documentation", "message": "Checking documentation quality..."})
            state = await loop.run_in_executor(None, run_documentation_agent, state)
            await websocket.send_json({
                "type": "agent_done", "agent": "documentation",
                "message": f"Documentation score: {state.documentation.score}/100",
                "data": {"score": state.documentation.score if state.documentation else 0}
            })

            # Step 6 — Synthesis
            await websocket.send_json({"type": "agent_start", "agent": "synthesis", "message": "Synthesizing final review report..."})
            state = await loop.run_in_executor(None, run_synthesis_agent, state)

            review = state.final_review
            if review:
                await websocket.send_json({
                    "type": "complete",
                    "agent": "synthesis",
                    "message": "Review complete",
                    "data": {
                        "pr_title":          state.parsed_pr.title,
                        "pr_author":         state.parsed_pr.author,
                        "repo":              state.parsed_pr.repo_name,
                        "overall_score":     review.overall_score,
                        "recommendation":    review.recommendation,
                        "summary":           review.summary,
                        "security_findings": [f.model_dump() for f in state.security_findings],
                        "logic_findings":    [f.model_dump() for f in state.logic_findings],
                        "test_coverage_score":  state.test_coverage.coverage_score if state.test_coverage else 0,
                        "documentation_score":  state.documentation.score if state.documentation else 0,
                        "security_highlights":  review.security_highlights,
                        "logic_highlights":     review.logic_highlights,
                        "top_suggestions":      review.top_suggestions,
                        "estimated_review_time_minutes": review.estimated_review_time_minutes,
                        "missing_test_cases": state.test_coverage.missing_test_cases if state.test_coverage else [],
                        "missing_docstrings":  state.documentation.missing_docstrings if state.documentation else [],
                        "missing_type_hints":  state.documentation.missing_type_hints if state.documentation else [],
                        "errors": state.errors,
                    }
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Synthesis failed: {state.errors}"
                })

        await run_with_progress()

    except WebSocketDisconnect:
        print("  [websocket] Client disconnected")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


def _fetch_pr_step(state, pr_url: str):
    from tools.github_client import fetch_pr
    try:
        state.parsed_pr = fetch_pr(pr_url)
    except Exception as e:
        state.errors.append(str(e))
    return state


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "PR Review Agent API",
        "endpoints": {
            "POST /review": "Submit PR URL, get full review (synchronous)",
            "WS   /review/stream": "Stream agent progress in real time",
            "GET  /health": "Health check",
            "GET  /docs": "Interactive API documentation",
        }
    }