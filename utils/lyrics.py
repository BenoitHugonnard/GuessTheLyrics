from pathlib import Path
import re
import random
import copy
from .settings import settings


current_dir = Path(__file__).parent


class Lyric:
    def __init__(self, idx, raw_str):
        self.idx = idx
        self.raw_str = raw_str
        self.ts, self.lyric = self.split_timestamp_lyric()
        self.ms = self.transfo_ts_to_ms()
        self.split_components, self.words_idx, self.punct_idx = self.split_lyric()

    def split_timestamp_lyric(self):
        m = re.match(r'(\[[0-9]+:[0-9]+\.[0-9]+\]) (.*)', self.raw_str)
        return m.group(1), m.group(2)

    def transfo_ts_to_ms(self):
        m = re.match(r'\[([0-9]+):([0-9]+)\.([0-9]+)\]', self.ts)
        ms = int(m.group(1)) * 60 * 1000
        ms += int(m.group(2)) * 1000
        ms += int(m.group(3)) * 10
        return ms

    def transfo_ms_to_ts(self, remove_ms=0):
        cur_ms = self.ms - remove_ms
        minutes = int(cur_ms / 1000 / 60)
        cur_ms = cur_ms - minutes * 1000 * 60
        seconds = int(cur_ms / 1000)
        cur_ms = cur_ms - seconds * 1000
        c_secs = int(cur_ms / 10)
        return f"[{minutes:02d}:{seconds:02d}.{c_secs:02d}]"

    def split_lyric(self):
        regexp = re.compile("[?!.',]|\w+")
        split_list = regexp.findall(self.lyric)
        words_idx = []
        punctuation_idx = []
        for idx, val in enumerate(split_list):
            if val in ("?", "!", ".", "'", ","):
                punctuation_idx.append(idx)
            else:
                words_idx.append(idx)
        return split_list, words_idx, punctuation_idx

    def generate_placeholder(self, split_idx=0):
        response = []
        for idx, val in enumerate(self.split_components):
            if idx in self.words_idx:
                word_idx = self.words_idx.index(idx)
                if word_idx < split_idx:
                    pass
                else:
                    response.append("___")
        return " ".join(response)

    def generate_initials(self, split_idx=0):
        response = []
        for idx, val in enumerate(self.split_components):
            if idx in self.words_idx:
                word_idx = self.words_idx.index(idx)
                if len(val) == 1:
                    response.append(val)
                else:
                    if word_idx < split_idx:
                        response.append(val)
                    else:
                        response.append(f"{val[0]}___")
            else:
                response.append(val)
        return " ".join(response)

    def generate_lyrics(self, split_idx=None):
        if split_idx is None:
            return f"{self.ts} {self.lyric}"

        response = []
        for idx, val in enumerate(self.split_components):
            if idx in self.words_idx:
                word_idx = self.words_idx.index(idx)
                if word_idx < split_idx:
                    response.append(val)
                else:
                    response.append(f"___")
            else:
                response.append(val)
        return f"{self.ts} " + " ".join(response)

    def generate_answer(self):
        return [self.split_components[word_idx]
                for word_idx in self.words_idx]


class Lyrics:
    def __init__(self, name):
        root_data_dir = current_dir.parent / "data"
        self.raw_path = root_data_dir / "raw" / name / "lyrics.txt"
        self.data_path = root_data_dir / "data" / name / "lyrics.txt"
        self.lyrics = [Lyric(idx, line) for idx, line in
                       enumerate(self.load_raw())]

    def load_raw(self):
        with open(self.raw_path, "r") as f:
            return [x.strip() for x in f.readlines()]

    def generate_break(self, break_idx=None):
        if not break_idx:
            lyrics_break = random.randint(10, len(self.lyrics))
            answer = self.lyrics[lyrics_break]
            raw_lyrics = [lyric.raw_str for lyric in
                          self.lyrics[:lyrics_break]]

        else:
            answer, raw_lyrics = None, [lyric.raw_str for lyric in self.lyrics]

        return answer, raw_lyrics

    def _split_lyrics(self):
        beginning_safety = settings.SPLIT_BEGIN_SAFETY
        ending_safety = settings.SPLIT_END_SAFETY

        # nb_breaks to compute
        nb_breaks = settings.MAX_LEVEL

        # new lyrics without beginning and ending
        lyrics = self.lyrics[beginning_safety:-ending_safety]

        # size of each blocks of lyrics
        split_size = int(len(lyrics) / nb_breaks)

        result = {}

        for break_idx in range(nb_breaks):
            start_idx = break_idx * split_size
            end_idx = (break_idx + 1) * split_size
            result[str(break_idx)] = [lyric for lyric in
                                      lyrics[start_idx:end_idx]]

        return result

    def _choose_possibility(self, lyrics, nb_words):
        possibilities = []

        for idx in range(1, len(lyrics)):
            cur_lyric = lyrics[idx]
            prev_lyric = lyrics[idx - 1]

            if len(cur_lyric.words_idx) >= nb_words:
                if all(cur_lyric.lyric not in x.lyric for x in self.lyrics[:cur_lyric.idx]):
                    possibility = [
                        (cur_lyric.idx, cur_lyric.words_idx[-nb_words:])]
                    possibilities.append(possibility)
                else:
                    print(cur_lyric.lyric, "already said")

            elif len(cur_lyric.words_idx) + len(
                    prev_lyric.words_idx) >= nb_words:
                if all(cur_lyric.lyric not in x.lyric for x in
                       self.lyrics[:cur_lyric.idx])\
                        and all(prev_lyric.lyric not in x.lyric for x in
                       self.lyrics[:prev_lyric.idx]):

                    final_size = len(cur_lyric.words_idx)
                    possibility = [
                        (prev_lyric.idx,
                         prev_lyric.words_idx[-(nb_words - final_size):]),
                        (cur_lyric.idx, cur_lyric.words_idx)
                    ]
                    possibilities.append(possibility)
                else:
                    print(cur_lyric.lyric, prev_lyric.lyric, "already said")
            else:
                print(cur_lyric.lyric, prev_lyric.lyric, "not good")
        if not possibilities:
            return []
        choice = random.choice(possibilities)
        print("CHOICE", choice)
        return choice

    def _generate_lyrics(self, choice, break_idx, prev_idx=None):
        lyrics_break_safety = settings.BREAK_SAFETY

        cut_idx = choice[0][0]
        choice_obj = copy.deepcopy(self.lyrics[cut_idx])

        if break_idx == 0:
            lyrics_to_show = [lyric.generate_lyrics()
                              for lyric in self.lyrics[:cut_idx]]

        else:
            begin_idx = prev_idx - lyrics_break_safety
            beginning_ms = self.lyrics[begin_idx].ms
            cur_lyrics = copy.deepcopy(self.lyrics[begin_idx:cut_idx])
            for lyric in cur_lyrics:
                lyric.ts = lyric.transfo_ms_to_ts(remove_ms=beginning_ms)
            lyrics_to_show = [lyric.generate_lyrics()
                              for lyric in cur_lyrics]
            choice_obj.ts = choice_obj.transfo_ms_to_ts(remove_ms=beginning_ms)

        nb_words_to_show = len(choice_obj.words_idx) - len(choice[0][1])
        lyrics_to_show.append(choice_obj.generate_lyrics(nb_words_to_show))

        print("LYRICS", lyrics_to_show)
        return lyrics_to_show

    def _generate_placeholder(self, choice):
        placeholder = []

        for idx, words_idx in choice:
            choice_obj = self.lyrics[idx]
            nb_words_to_show = len(choice_obj.words_idx) - len(words_idx)
            placeholder.append(
                choice_obj.generate_placeholder(nb_words_to_show))

        print("PLACEHOLDER", placeholder)
        return "\n".join(placeholder)

    def _generate_initials(self, choice):
        initials = []

        for idx, words_idx in choice:
            choice_obj = self.lyrics[idx]
            nb_words_to_show = len(choice_obj.words_idx) - len(words_idx)
            initials.append(
                choice_obj.generate_initials(nb_words_to_show))

        print("INITIALS", initials)
        return "\n".join(initials)

    def _generate_answer(self, choice):
        answer = []

        for idx, words_idx in choice:
            choice_obj = self.lyrics[idx]
            answer.extend(choice_obj.split_components[word_idx]
                          for word_idx in words_idx)

        print("ANSWER", answer)
        return answer

    def generate_breaks(self):
        mapping_breaks = settings.mapping_level()
        print(mapping_breaks)
        result = {}
        for break_idx, lyrics in self._split_lyrics().items():
            print("BREAK IDX", break_idx)
            nb_words = mapping_breaks[break_idx]
            choice = self._choose_possibility(lyrics, nb_words)
            if choice:
                prev_idx = int(break_idx) - 1 if int(break_idx) else None
                prev_break_idx = result.get(str(prev_idx), {}).get("break_idx", 0)
                lyrics_to_show = self._generate_lyrics(choice, int(break_idx),
                                                       prev_idx=prev_break_idx)
                placeholder = self._generate_placeholder(choice)
                initials = self._generate_initials(choice)
                answer = self._generate_answer(choice)

                result[break_idx] = {
                    "break_idx": choice[0][0],
                    "previous_break_timestamp": result.get(str(prev_idx), {}).get(
                        "break_timestamp", 0),
                    "break_timestamp": self.lyrics[choice[0][0]].ms,
                    "lyrics_to_show": lyrics_to_show,
                    "placeholder": placeholder,
                    "initials": initials,
                    "level": str(break_idx),
                    "answer": answer
                }
            else:
                break
        return result
