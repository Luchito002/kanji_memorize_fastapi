from enum import Enum

class SRSStatus(str, Enum):
    learning = "learning"       # New kanji that hasn't been consolidated yet
    review = "review"           # Previously learned, currently under review
    relearning = "relearning"   # After a failed recall, back to relearning phase
    mastered = "mastered"       # Recalled multiple times, now in spaced repetition
    suspended = "suspended"     # No longer reviewed, paused by user decision
