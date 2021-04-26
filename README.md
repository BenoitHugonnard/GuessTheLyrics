# Guess the Words !

## Setup

- You need docker + docker-compose installed.
- If you want to overwrite localhost as domain, create a file `docker.env` with line `DOMAIN=<ip|dns>`

## Play

Once the steps described in the next chapter, you can play in 3 modes:
- Classic: one verse is randomly chosen, you need to guess the words
- Ladder: you have multi level (5 by default) and a growing number of words to find
- Karaoke: The song and the lyrics, no guessing

## Data organization

The data directory is where everything will be stored (songs, lyrics, images)

```bash
data
├── config.yaml
├── data
├── images
│   └── France.png
└── raw
    └── angele-balance_ton_quoi
        ├── lyrics.txt
        └── song.mp3
```

`config.yaml`: will need an entry by "song_id"
```yaml
angele-balance_ton_quoi:
  author: Angele
  title: Balance ton Quoi
  categories:
    - France
```

`images`: directory containing a PNG file by category

`raw`: directory containing one directory by "song_id" with the `lyrics.txt` file (LRC format) and a `song.mp3` file.

When you want to add a new song, you'll need to complete all previous parts.
