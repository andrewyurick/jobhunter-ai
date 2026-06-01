import os
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from jobhunter_agent.agent import root_agent


APP_NAME = os.getenv("APP_NAME", "jobhunter_ai")

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def ensure_session(user_id: str, session_id: str) -> None:
    try:
        existing = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        if existing:
            return
    except Exception:
        pass

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )


async def call_agent(
    message: str,
    user_id: str,
    session_id: str | None = None,
) -> dict:
    if not session_id:
        session_id = str(uuid.uuid4())

    await ensure_session(user_id=user_id, session_id=session_id)

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    final_text = "No final response was produced."

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text or final_text
            break

    return {
        "session_id": session_id,
        "user_id": user_id,
        "response": final_text,
    }