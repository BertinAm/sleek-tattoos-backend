"""Keyword-matching FAQ bot — ports the frontend's matchAnswer() so the
support widget still gets an instant reply, now generated server-side
against the live FAQ table instead of a hardcoded JS array."""
from content.models import FAQ

FALLBACK_ANSWER = (
    "Great question! Our team will confirm every detail during your free consultation. "
    "Whatever you're picturing, we'll make it happen with premium care and zero pressure to pay anything upfront."
)


def match_answer(text: str) -> str:
    t = text.lower()
    words = [w for w in t.split(' ') if len(w) > 3]
    for faq in FAQ.objects.all():
        q_lower = faq.question.lower()
        if any(w in q_lower for w in words):
            return faq.answer
    return FALLBACK_ANSWER


GREETING = "Hi! I'm here to answer questions and reassure you about booking with Sleek Tattoos. Ask me anything."
