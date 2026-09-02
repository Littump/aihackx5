from app.core.errors import AppError, error_body


def test_app_error_carries_code_and_status() -> None:
    error = AppError("user_not_found", "Пользователь 42 не найден", status=404)
    assert error.code == "user_not_found"
    assert error.status == 404
    assert str(error) == "Пользователь 42 не найден"


def test_error_body_shape() -> None:
    assert error_body("x", "y") == {"error": {"code": "x", "message": "y"}}
