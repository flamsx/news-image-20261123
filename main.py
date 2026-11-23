"""main.py — news-image-20261123 v1 entry program (fresh build).

Writes one image to /output/entry.png (or ./output/entry.png locally).
Stories researched fresh for Monday 23 November 2026; see
../story-bank/news-image-20261123.json for sources and first-report dates.
Canvas 1024x1024 per the kit rules. Lexend for all text.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import render  # noqa: E402

LEADS = [
    {
        "num": 1, "scene": "globe", "banner": "COP31: NO DEAL",
        "tag": "ANTALYA  ·  CLIMATE",
        "headline": "COP31 collapses with no deal",
        "deck": "No deal after record overtime; UN chief 'deeply disappointed'; $120bn goal dropped.",
        "source": "Reuters, CNN", "pin": (30.7, 36.9),
    },
    {
        "num": 2, "scene": "drone", "banner": "DYMER",
        "tag": "KYIV REGION  ·  WAR",
        "headline": "Russian drone flattens flats near Kyiv",
        "deck": "Drone flattens part of a five-storey block; five dead, about nine missing.",
        "source": "Reuters", "pin": (30.3, 50.8),
    },
    {
        "num": 3, "scene": "tanker", "banner": "HORMUZ",
        "tag": "STRAIT OF HORMUZ  ·  SHIPPING",
        "headline": "Three tankers hit in Hormuz",
        "deck": "Three tankers hit in two days; 22 attacks in November, the second-highest count of the war.",
        "source": "AP, CNN", "pin": (56.5, 26.5),
    },
]

MEDIUMS = [
    {
        "num": 4, "scene": "plane", "banner": "DELTA",
        "tag": "ATLANTA  ·  TRAVEL",
        "headline": "Delta meltdown delays 1,000+ flights",
        "deck": "Automation failure hits weight checks; 67% of flights delayed.",
        "source": "AP", "pin": (-84.4, 33.7),
    },
    {
        "num": 5, "scene": "fire", "banner": "SERANG",
        "tag": "INDONESIA  ·  DISASTER",
        "headline": "Factory fire kills three, 36 missing",
        "deck": "Blaze at the Milkita candy factory; 300 workers were inside.",
        "source": "AP", "pin": (106.1, -6.1),
    },
    {
        "num": 6, "scene": "baseball", "banner": "SKUBAL",
        "tag": "NEW YORK  ·  BASEBALL",
        "headline": "Skubal signs record $450m Mets deal",
        "deck": "Nine years, $450m — the richest pitcher contract ever.",
        "source": "AP", "pin": (-74.0, 40.7),
    },
    {
        "num": 7, "scene": "bike", "banner": "MARQUEZ",
        "tag": "PORTIMAO  ·  MOTOGP",
        "headline": "Marquez seals eighth MotoGP title",
        "deck": "Eighth crown after a 102-point comeback; equals Agostini.",
        "source": "MotoGP.com", "pin": (-8.5, 37.1),
    },
    {
        "num": 8, "scene": "handshake", "banner": "DELHI",
        "tag": "INDIA  ·  DIPLOMACY",
        "headline": "Nepal PM meets Modi in Delhi today",
        "deck": "First bilateral visit; energy, rail and hydropower deals.",
        "source": "The Hindu", "pin": (77.2, 28.6),
    },
    {
        "num": 9, "scene": "capitol", "banner": "258 SEATS",
        "tag": "WASHINGTON  ·  POLITICS",
        "headline": "Democrats clinch 258 House seats",
        "deck": "Biggest House majority since 1992; Jeffries set to be speaker.",
        "source": "AP", "pin": (-77.0, 38.9),
    },
    {
        "num": 10, "scene": "virus", "banner": "MEASLES",
        "tag": "UNITED STATES  ·  HEALTH",
        "headline": "US loses measles-free status",
        "deck": "Cases hit the highest rate in decades; babies born with measles.",
        "source": "AP", "pin": (-98.0, 39.8),
    },
    {
        "num": 11, "scene": "planet", "banner": "MERCURY",
        "tag": "SPACE  ·  SCIENCE",
        "headline": "Two spacecraft reach Mercury orbit",
        "deck": "A pair of craft loop into orbit; first visitors in years.",
        "source": "AP", "pin": None,
    },
    {
        "num": 12, "scene": "euro", "banner": "BRUSSELS",
        "tag": "EUROPE  ·  ECONOMY",
        "headline": "EU proposes tax on big tech",
        "deck": "Brussels proposes a tax on big tech in its new budget draft.",
        "source": "NDTV", "pin": (4.4, 50.8),
    },
    {
        "num": 13, "scene": "cricket", "banner": "720/9",
        "tag": "WELLINGTON  ·  CRICKET",
        "headline": "India pile up record 720 in Wellington",
        "deck": "Highest Test total on New Zealand soil; Pant hits 128.",
        "source": "ANI", "pin": (174.8, -41.3),
    },
]

BRIEFS = [
    {"num": 14, "headline": "Nine shot at California concert", "source": "AP", "pin": (-119.2, 36.1)},
    {"num": 15, "headline": "Army to detonate unstable chemicals", "source": "AP", "pin": (-93.1, 41.9)},
    {"num": 16, "headline": "Poland: Russia twice tried to kill rapper", "source": "AP", "pin": (21.0, 52.2)},
    {"num": 17, "headline": "Blast on Russian ship at Libya port", "source": "BBC", "pin": (20.0, 31.0)},
    {"num": 18, "headline": "Missile hits Kryvyi Rih, two killed", "source": "AP", "pin": (33.4, 47.9)},
    {"num": 19, "headline": "Liverpool rout United 4-0", "source": "Sportradar", "pin": (-3.0, 53.4)},
    {"num": 20, "headline": "Cartel chief captured, 11 dead", "source": "AP", "pin": (-107.4, 24.8)},
    {"num": 21, "headline": "Pentagon limits Canada military ties", "source": "AP", "pin": (-75.7, 45.4)},
    {"num": 22, "headline": "China slams US telecom ban", "source": "Manila Times", "pin": (116.4, 39.9)},
    {"num": 23, "headline": "Seoul education chief quits over AI cheating", "source": "Manila Times", "pin": (127.0, 37.5)},
    {"num": 24, "headline": "Myanmar slams ASEAN decision", "source": "Jagran Josh", "pin": (96.0, 19.8)},
    {"num": 25, "headline": "Houses torched in Bangladesh violence", "source": "Mathrubhumi", "pin": (90.4, 23.8)},
    {"num": 26, "headline": "Lacson slams P241bn 'aid' in budget", "source": "Manila Times", "pin": (121.0, 14.6)},
    {"num": 27, "headline": "Eala tops win rate vs top 10", "source": "Manila Times", "pin": (121.2, 14.4)},
    {"num": 28, "headline": "Miss Universe prelims held in San Juan", "source": "Pageant Circle", "pin": (-66.1, 18.5)},
    {"num": 29, "headline": "Pope hit by rosary on popemobile ride", "source": "AP", "pin": (-60.0, -15.0)},
    {"num": 30, "headline": "Kenya minerals deal goes to US group", "source": "BBC", "pin": (36.8, -1.3)},
    {"num": 31, "headline": "Stroke cases rise among young in Singapore", "source": "Straits Times", "pin": (103.8, 1.35)},
    {"num": 32, "headline": "ANC fights to hold South Africa cities", "source": "BBC", "pin": (28.0, -26.0)},
    {"num": 33, "headline": "Bayelsa boat toll rises to 29", "source": "Channels TV", "pin": (6.3, 4.8)},
    {"num": 34, "headline": "Kenya confirms ninth Ebola case", "source": "Yeni Safak", "pin": (37.2, -1.0)},
    {"num": 35, "headline": "Egypt condemns attacks on Bahrain", "source": "Daily News Egypt", "pin": (50.6, 26.2)},
]

STATS = [
    ("258", "House seats won by\nDemocrats (AP)"),
    ("$450m", "Skubal's record\npitcher deal (AP)"),
    ("1,000+", "Delta flights delayed\non Sunday (AP)"),
    ("36", "missing after the\nIndonesia factory fire (AP)"),
    ("5", "dead in the Dymer\ndrone strike (Reuters)"),
    ("22", "tanker attacks in\nHormuz in November (CNN)"),
]

REGIONS = [
    ("Europe", 6), ("Asia", 9), ("Middle East", 2), ("Africa", 5),
    ("Americas", 10), ("Oceania", 1), ("Global", 2),
]

DATE_CHECK = (
    "Left out, first reported before today: Anthropic's market debut (19 Nov), "
    "the Pete Rose pardon (19 Nov), Grand Theft Auto VI's arrival (19 Nov), "
    "Denmark's expulsion of a Russian diplomat (20 Nov), the FBI crime-database hack (20 Nov). "
    "Not yet: the Miss Universe final (Tue 24 Nov)."
)

FOOTER = "Every story here happened, or was first reported, on Monday 23 November 2026."


def main():
    out_dir = "/output" if os.path.isdir("/output") else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    img = render(LEADS, MEDIUMS, BRIEFS, STATS, REGIONS, DATE_CHECK, FOOTER)
    path = os.path.join(out_dir, "entry.png")
    img.save(path, format="PNG")
    print(f"wrote {path} {img.size} mode={img.mode}")
    return path


if __name__ == "__main__":
    main()
