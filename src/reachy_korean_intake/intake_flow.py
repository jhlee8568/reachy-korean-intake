"""Three-question intake state, independent of speech generation."""

import re
from dataclasses import field, dataclass


QUESTIONS = (
    "지금 어디가 불편하세요?",
    "그 증상은 언제부터 시작됐나요?",
    "불편한 정도를 0에서 10까지 숫자로 말해 주세요.",
)


@dataclass
class IntakeFlow:
    """Keep question order and transition to small talk explicit."""

    phase: str = "idle"
    index: int = 0
    retries: int = 0
    answers: list[str] = field(default_factory=list)

    def start(self) -> str:
        """Begin a fresh intake and clear previous answers."""
        self.phase, self.index, self.retries = "intake", 0, 0
        self.answers.clear()
        return "안녕하세요. 간단한 질문 세 가지를 드릴게요. " + QUESTIONS[0]

    def stop(self) -> None:
        """Stop listening and discard answers."""
        self.phase = "stopped"
        self.answers.clear()

    def accept(self, text: str) -> str | None:
        """Return the next scripted utterance, or None for small talk."""
        compact = re.sub(r"[\s.!?]", "", text)
        if compact in {"그만", "그만해", "그만할게요", "중단", "대화종료", "종료", "멈춰"}:
            self.stop()
            return "대화를 마칠게요. 편안한 하루 보내세요."
        if compact in {"다시시작", "문진시작", "다시시작해줘"}:
            return self.start()
        if self.phase == "smalltalk":
            return None
        if self.phase != "intake":
            return ""
        score_words = {
            "영": 0,
            "공": 0,
            "일": 1,
            "이": 2,
            "삼": 3,
            "사": 4,
            "오": 5,
            "육": 6,
            "칠": 7,
            "팔": 8,
            "구": 9,
            "십": 10,
            "열": 10,
        }
        score_match = re.fullmatch(
            r"(10|[0-9]|영|공|일|이|삼|사|오|육|칠|팔|구|십|열)(?:점)?(?:정도)?(?:이에요|예요|이요|요|입니다)?",
            compact,
        )
        if not text.strip() or (self.index == 2 and score_match is None):
            self.retries += 1
            if self.retries >= 2:
                self.stop()
                return "답변을 확인하기 어려워 문진을 잠시 멈출게요. 다시 시작 버튼을 눌러 주세요."
            return "잘 듣지 못했어요. " + QUESTIONS[self.index]
        self.answers.append(text)
        self.retries = 0
        self.index += 1
        if self.index == 3:
            self.phase = "smalltalk"
            assert score_match is not None
            token = score_match.group(1)
            score = int(token) if token.isdigit() else score_words[token]
            reaction = "많이 불편하시겠어요." if score >= 7 else "불편한 정도를 알겠어요."
            return reaction + " 문진이 끝났어요. 답변해 주셔서 감사합니다. 쉬실 때는 주로 무엇을 하세요?"
        reaction = "불편하셨겠어요." if self.index == 1 else "시작 시점을 알겠어요."
        return reaction + " " + QUESTIONS[self.index]
