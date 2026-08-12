"""Project C routing / planner / insights smoke tests."""

from __future__ import annotations

from src.agent.planner import plan_tools
from src.analyzer.classifier import analyze_request
from src.insights.service import RiskInsightRequest, build_insight_prompt, generate_insight
from src.insights.store import clear_insights, list_insights, record_insight
from src.models import RequestType
from src.routing.engine import route_chat


def test_classify_simple() -> None:
    assert analyze_request("오늘 날씨 알려줘") == RequestType.SIMPLE


def test_classify_complex() -> None:
    assert analyze_request("아키텍처 비교 분석이 필요해. 근거를 들어 설명해.") == RequestType.COMPLEX_REASONING


def test_plan_db_write() -> None:
    plans = plan_tools("유저 role을 admin으로 바꿔")
    assert any(p.tool == "db_write" for p in plans)


def test_plan_search() -> None:
    plans = plan_tools("서울 날씨 찾아줘")
    assert plans[0].tool == "search"


def test_route_chat_without_security() -> None:
    response = route_chat("hello", enable_security=False, persist=False)
    assert response.blocked is False
    assert response.content
    assert response.used_model.value in {"gpt", "claude", "gemini"}


def test_insight_generation() -> None:
    clear_insights()
    req = RiskInsightRequest(
        source="news",
        entity_id="a-1",
        risk_score=77.0,
        label="high",
        signals=["weak_evidence"],
        context={"title": "테스트"},
        enable_security=False,
    )
    prompt = build_insight_prompt(req)
    assert "뉴스 신뢰도" in prompt
    insight = record_insight(generate_insight(req))
    assert insight.entity_id == "a-1"
    assert list_insights(limit=1)
