from sandbox_engine import SecureSandbox


def test_execute_code_runs_in_local_process():
    result = SecureSandbox().execute_code("print('hi')")
    assert "Local Python execution successful" in result
    assert "hi" in result
