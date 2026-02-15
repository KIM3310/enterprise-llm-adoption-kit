from app.llm_adapter import StubLLMAdapter


def test_stub_adapter_generates_uc1_and_uc2_without_regex_errors() -> None:
    adapter = StubLLMAdapter()

    uc1_messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "Summarize architecture risks and propose next steps."},
        {
            "role": "assistant",
            "content": "CONTEXT:\n[ARC-1001:summary] Payments prod gateway depends on redis.\n[ARC-1001:runbook_steps] Check latency dashboard.",
        },
    ]
    uc1 = adapter.generate(uc1_messages, use_case="uc1")
    assert isinstance(uc1.text, str) and uc1.text
    assert uc1.tokens_in > 0
    assert uc1.tokens_out > 0

    uc2_messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "Analyze the logs and propose root causes."},
        {
            "role": "assistant",
            "content": "CONTEXT:\nLOGS:\nERROR Timeout while calling payments API\nSIGNATURES: ['Timeout while']\nRUNBOOK: ['Check upstream latency']\n",
        },
    ]
    uc2 = adapter.generate(uc2_messages, use_case="uc2")
    assert isinstance(uc2.text, str) and uc2.text
    assert uc2.tokens_in > 0
    assert uc2.tokens_out > 0

