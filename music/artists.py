"""Artist pool for autoplay shuffle \u2014 diverse random music."""
from __future__ import annotations

import random

# ~200 diverse artists across genres and countries
_ARTISTS = [
    # Pop
    "Taylor Swift", "Ed Sheeran", "Adele", "Bruno Mars", "Dua Lipa",
    "The Weeknd", "Harry Styles", "Billie Eilish", "Olivia Rodrigo", "Ariana Grande",
    "Justin Bieber", "Shawn Mendes", "Camila Cabello", "Selena Gomez", "Halsey",
    "Doja Cat", "Lizzo", "Charlie Puth", "Sam Smith", "Lauv",
    # R&B / Soul
    "SZA", "Daniel Caesar", "H.E.R.", "Khalid", "Frank Ocean",
    "The Marias", "Giveon", "Summer Walker", "Brent Faiyaz", "Jhene Aiko",
    # Rock / Alternative
    "Arctic Monkeys", "Tame Impala", "The 1975", "Imagine Dragons", "Coldplay",
    "Radiohead", "Muse", "Green Day", "Paramore", "Twenty One Pilots",
    "Red Hot Chili Peppers", "Foo Fighters", "Linkin Park", "Oasis", "Nirvana",
    # Hip Hop / Rap
    "Kendrick Lamar", "Drake", "Travis Scott", "Tyler The Creator", "J. Cole",
    "Mac Miller", "Post Malone", "Kanye West", "Eminem", "Anderson .Paak",
    # Electronic / EDM
    "Daft Punk", "ODESZA", "Flume", "Disclosure", "Kygo",
    "Marshmello", "Illenium", "Porter Robinson", "Madeon", "Rufus Du Sol",
    # Jazz / Neo-Soul
    "Norah Jones", "Tom Misch", "FKJ", "Jorja Smith", "Erykah Badu",
    "Robert Glasper", "Esperanza Spalding", "Kamasi Washington", "Chet Baker", "Bill Evans",
    # Latin
    "Bad Bunny", "J Balvin", "Rosalia", "Shakira", "Ozuna",
    "Daddy Yankee", "Maluma", "Karol G", "Rauw Alejandro", "Becky G",
    # K-Pop
    "BTS", "BLACKPINK", "Stray Kids", "NewJeans", "TWICE",
    "IVE", "aespa", "EXO", "Red Velvet", "SEVENTEEN",
    "(G)I-DLE", "LE SSERAFIM", "TXT", "ATEEZ", "ENHYPEN",
    # J-Pop / J-Rock
    "YOASOBI", "Kenshi Yonezu", "Ado", "ONE OK ROCK", "LiSA",
    "Aimer", "Official HIGE DANdism", "Mrs. GREEN APPLE", "Fujii Kaze", "imase",
    # Indonesian
    "Tulus", "Pamungkas", "Hindia", "Sal Priadi", "Nadin Amizah",
    "Raisa", "Isyana Sarasvati", "Fiersa Besari", "Ardhito Pramono", "Bernadya",
    "Maliq & D'Essentials", "Sheila on 7", "Dewa 19", "NOAH", "Peterpan",
    "Reality Club", "Feast", ".Feast", "Banda Neira", "White Shoes & The Couples Company",
    "Efek Rumah Kaca", "Elephant Kind", "Kunto Aji", "Rendy Pandugo", "GAC",
    "Andmesh", "Mahalini", "Lyodra", "Tiara Andini", "Juicy Luicy",
    "Weird Genius", "NIKI", "Rich Brian", "Warren Hue", "Stephanie Poetri",
    # Thai
    "Phum Viphurit", "Milli", "Stamp", "Bodyslam", "Palmy",
    # Country / Folk
    "John Mayer", "Hozier", "Bon Iver", "Iron & Wine", "Fleet Foxes",
    # Classic / Timeless
    "Queen", "The Beatles", "Michael Jackson", "Whitney Houston", "Stevie Wonder",
    "Marvin Gaye", "Prince", "David Bowie", "Elton John", "ABBA",
    # Acoustic / Indie
    "Cigarettes After Sex", "Lana Del Rey", "Phoebe Bridgers", "Clairo", "beabadoobee",
    "Rex Orange County", "Boy Pablo", "Men I Trust", "Mac DeMarco", "Khruangbin",
    # Chinese / Mandopop
    "Jay Chou", "JJ Lin", "G.E.M.", "Eric Chou", "Crowd Lu",
    # Misc Global
    "Stromae", "Angele", "Aya Nakamura", "Burna Boy", "Wizkid",
    "Rema", "Tems", "Peso Pluma", "Feid", "Mora",
]

_SEARCH_TEMPLATES = [
    "{artist} official audio",
    "{artist} official music video",
    "{artist} lyrics",
    "{artist} song",
    "{artist} audio",
    "{artist} live performance",
]


def get_random_query(exclude_artists: set[str] | None = None) -> tuple[str, str]:
    """Get a random artist + search query for autoplay.

    Returns (query, artist_name).
    """
    pool = _ARTISTS.copy()
    if exclude_artists:
        pool = [a for a in pool if a not in exclude_artists]
    if not pool:
        pool = _ARTISTS.copy()

    artist = random.choice(pool)
    template = random.choice(_SEARCH_TEMPLATES)
    return template.format(artist=artist), artist
