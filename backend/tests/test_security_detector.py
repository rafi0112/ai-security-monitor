import pytest

from app.ml.detector import (
    SecurityDetector,
    LoginEvent
)


@pytest.mark.asyncio
async def test_bruteforce_detection():

    detector = SecurityDetector()

    # Simulate repeated failed logins
    for i in range(12):

        event = LoginEvent(
            ip_address="192.168.1.100",
            username="admin",
            success=False,
            user_agent="python-requests"
        )

        result = await detector.analyze_login(event)

    assert result.attack_type == "brute_force"
    assert result.should_block is True
    assert result.risk_score >= 0.7