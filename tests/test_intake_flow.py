"""Behavior of the Korean intake, independent of the language model."""

from reachy_korean_intake.intake_flow import QUESTIONS, IntakeFlow


def test_three_answers_then_smalltalk() -> None:
    """Exactly three accepted answers move the app to small talk."""
    flow = IntakeFlow()
    assert QUESTIONS[0] in flow.start()
    assert QUESTIONS[1] in str(flow.accept("배가 아파요"))
    assert QUESTIONS[2] in str(flow.accept("어제부터요"))
    assert "문진이 끝났어요" in str(flow.accept("삼 점이요"))
    assert flow.phase == "smalltalk"
    assert flow.accept("음악 듣는 걸 좋아해요") is None
    assert flow.index == 3


def test_invalid_score_never_fabricates_answer() -> None:
    """Keep prompting for a valid score without losing previous answers."""
    flow = IntakeFlow()
    flow.start()
    flow.accept("머리가 아파요")
    flow.accept("오늘요")
    for answer in ["13점", "잘 모르겠어요", "", "많이 아파요", "-1"]:
        assert flow.accept(answer) == "0부터 10까지의 숫자로 말해주실 수 있으시겠어요?"
        assert flow.index == 2
        assert flow.phase == "intake"
        assert flow.answers == ["머리가 아파요", "오늘요"]
    assert "문진이 끝났어요" in str(flow.accept("5점"))
    assert flow.phase == "smalltalk"
    assert flow.answers == ["머리가 아파요", "오늘요", "5점"]


def test_stop_while_waiting_for_score() -> None:
    """Explicit stop still ends intake while a valid score is pending."""
    flow = IntakeFlow()
    flow.start()
    flow.accept("머리가 아파요")
    flow.accept("오늘요")
    flow.accept("잘 모르겠어요")
    flow.accept("그만")
    assert flow.phase == "stopped"
    assert flow.answers == []


def test_stop_and_restart_clear_answers() -> None:
    """A new session never retains the preceding answers."""
    flow = IntakeFlow()
    flow.start()
    flow.accept("목이 아파요")
    flow.accept("그만")
    assert flow.phase == "stopped"
    assert flow.answers == []
    assert QUESTIONS[0] in str(flow.accept("다시 시작"))
    assert flow.index == 0
