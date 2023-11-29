import enum


class FeedStatus(str, enum.Enum):
    OK = "OK"
    FETCHING = "FETCHING"
    GONE = "GONE"
    NOT_FOUND = "NOT_FOUND"
    FAILED = "FAILED"
    TRY_LATER = "TRY_LATER"