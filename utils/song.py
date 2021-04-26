from pathlib import Path
from pydub import AudioSegment
import os

current_dir = Path(__file__).absolute().parent


class Song:
    def __init__(self, name):
        root_data_dir = current_dir.parent / "data"
        self.raw_path = root_data_dir / "raw" / name / "song.mp3"
        self.data_dir = root_data_dir / "data" / name
        self.song = AudioSegment.from_mp3(self.raw_path)

    def export_trimmed(self, break_timestamp):
        os.makedirs(self.data_dir, exist_ok=True)
        self.song[0:break_timestamp].export(self.data_dir / "song.mp3")

    def export_ladder_trimmed(self, idx, beginning_ts, ending_ts):
        print("EXPORTING", idx, beginning_ts, ending_ts)
        os.makedirs(self.data_dir, exist_ok=True)
        self.song[beginning_ts:ending_ts].export(self.data_dir / f"song-{idx}.mp3")
