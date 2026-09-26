from main import BASE_SYSTEM_PROMPT


def test_final_answers_follow_user_language():
    assert "same language" in BASE_SYSTEM_PROMPT
    assert "requested language" in BASE_SYSTEM_PROMPT
    assert "Only provide a translation" in BASE_SYSTEM_PROMPT