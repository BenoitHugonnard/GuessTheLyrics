from pydantic import BaseSettings
from random import randint


class Settings(BaseSettings):
    DOMAIN: str = "localhost"
    MAX_LEVEL: int
    LEVEL_0_WORDS: str
    LEVEL_1_WORDS: str
    LEVEL_2_WORDS: str
    LEVEL_3_WORDS: str
    LEVEL_4_WORDS: str
    SPLIT_BEGIN_SAFETY: int
    SPLIT_END_SAFETY: int
    BREAK_SAFETY: int

    def mapping_level(self):
        result = {}
        for idx in range(self.MAX_LEVEL):
            min_, max_ = getattr(self, f"LEVEL_{idx}_WORDS").split(",")
            min_, max_ = int(min_), int(max_)
            print(min_, max_)
            result[str(idx)] = randint(min_, max_)

        return result


settings = Settings()
