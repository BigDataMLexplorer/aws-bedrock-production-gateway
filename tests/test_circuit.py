from app.resilience import CircuitBreaker


def test_circuit_opens_after_threshold():
    c=CircuitBreaker(2,100)
    assert c.record_failure("m") is False
    assert c.record_failure("m") is True
    assert c.is_open("m") is True


def test_success_resets_circuit():
    c=CircuitBreaker(1,100);c.record_failure("m");c.record_success("m")
    assert c.is_open("m") is False
