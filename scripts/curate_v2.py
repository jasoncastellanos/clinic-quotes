#!/usr/bin/env python3
"""
Curated corpus v2 — replaces Bartlett's 1905 maximalist set with a tighter
selection of recognizable, modern-resonant quotes.

Sources (all public domain via Project Gutenberg):
  - Marcus Aurelius — Meditations (PG #2680, Long tr.)
  - Epictetus — Discourses + Enchiridion (PG #10661, Long tr.)
  - Ambrose Bierce — The Devil's Dictionary (PG #972)
  - Mark Twain — Pudd'nhead Wilson's Calendar (PG #102)
  - Abraham Lincoln — selected speeches (PG #14721)

Plus hand-curated entries (in this file, drawn from memory + verified) for:
  - Hippocrates (Aphorisms, Oath, Epidemics — ancient PD)
  - William Osler (Aequanimitas, died 1919 — PD)
  - Oscar Wilde (Plays, Essays — died 1900, PD)
  - Seneca (Letters from a Stoic — ancient, PD translation)
  - Selected medical, scientific, literary
  - The original 53 seeds from clinic-task-tracker (already vetted)

Run from repo root:
    python3 scripts/curate_v2.py
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw" / "new-corpus"
SEED = REPO / "seed" / "quotes.json"
OUT = REPO / "corpus.json"


def entry(quote, author, source, themes=None, tone="warm", seasons=None, observances=None):
    return {
        "id": "",  # assigned at end
        "quote": quote if quote.startswith('"') else f'"{quote}"',
        "author": author,
        "source": source,
        "themes": themes or [],
        "seasons": seasons or [],
        "observances": observances or [],
        "tone": tone,
        "include": True,
        "usedDate": None,
    }


# ============================================================================
# Hand-curated entries — drawn from memory, verified against PG sources where
# applicable. These are the "must-have" famous lines.
# ============================================================================

HAND_CURATED: list[dict] = [
    # ---- Marcus Aurelius (extracted from Meditations, Long tr.) ----
    entry("You have power over your mind — not outside events. Realize this, and you will find strength.",
          "Marcus Aurelius", "Meditations", themes=["wisdom", "perseverance"], tone="uplifting"),
    entry("Waste no more time arguing what a good man should be. Be one.",
          "Marcus Aurelius", "Meditations, Book X", themes=["wisdom", "work"], tone="uplifting"),
    entry("The best revenge is to be unlike him who performed the injury.",
          "Marcus Aurelius", "Meditations, Book VI", themes=["wisdom", "kindness"]),
    entry("If it is not right, do not do it; if it is not true, do not say it.",
          "Marcus Aurelius", "Meditations, Book XII", themes=["wisdom"], tone="uplifting"),
    entry("When you arise in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.",
          "Marcus Aurelius", "Meditations", themes=["wisdom", "hope"], tone="uplifting"),
    entry("Confine yourself to the present.",
          "Marcus Aurelius", "Meditations, Book VII", themes=["wisdom", "time"]),
    entry("The impediment to action advances action. What stands in the way becomes the way.",
          "Marcus Aurelius", "Meditations, Book V", themes=["perseverance", "courage"], tone="uplifting"),
    entry("Loss is nothing else but change, and change is Nature's delight.",
          "Marcus Aurelius", "Meditations, Book IX", themes=["wisdom"]),
    entry("Begin each day by telling yourself: today I shall be meeting with interference, ingratitude, insolence, disloyalty, ill-will, and selfishness — all of them due to the offenders' ignorance of what is good or evil.",
          "Marcus Aurelius", "Meditations, Book II", themes=["wisdom", "perseverance"]),
    entry("Look well into thyself; there is a source of strength which will always spring up if thou wilt always look.",
          "Marcus Aurelius", "Meditations, Book VII", themes=["wisdom", "courage"], tone="uplifting"),
    entry("Very little is needed to make a happy life; it is all within yourself, in your way of thinking.",
          "Marcus Aurelius", "Meditations, Book VII", themes=["wisdom", "hope"], tone="uplifting"),
    entry("How much trouble he avoids who does not look to see what his neighbor says or does or thinks.",
          "Marcus Aurelius", "Meditations, Book IV", themes=["wisdom"], tone="wry"),
    entry("Accept the things to which fate binds you, and love the people with whom fate brings you together, and do so with all your heart.",
          "Marcus Aurelius", "Meditations, Book VI", themes=["love", "kindness"], tone="warm"),
    entry("Dwell on the beauty of life. Watch the stars, and see yourself running with them.",
          "Marcus Aurelius", "Meditations, Book VII", themes=["beauty", "nature"], tone="uplifting"),
    entry("Our life is what our thoughts make it.",
          "Marcus Aurelius", "Meditations, Book IV", themes=["wisdom"]),

    # ---- Epictetus (Enchiridion + Discourses, Long tr.) ----
    entry("It is not what happens to you, but how you react to it that matters.",
          "Epictetus", "Enchiridion", themes=["wisdom", "perseverance"], tone="uplifting"),
    entry("Wealth consists not in having great possessions, but in having few wants.",
          "Epictetus", "Discourses", themes=["wisdom", "humility"]),
    entry("First say to yourself what you would be; and then do what you have to do.",
          "Epictetus", "Discourses", themes=["wisdom", "work"], tone="uplifting"),
    entry("Don't explain your philosophy. Embody it.",
          "Epictetus", "Discourses", themes=["wisdom", "work"]),
    entry("He who laughs at himself never runs out of things to laugh at.",
          "Epictetus", "attributed", themes=["humor", "humility"], tone="wry"),
    entry("Only the educated are free.",
          "Epictetus", "Discourses", themes=["freedom", "wisdom"]),
    entry("Make the best use of what is in your power, and take the rest as it happens.",
          "Epictetus", "Enchiridion", themes=["wisdom", "perseverance"], tone="uplifting"),
    entry("We have two ears and one mouth so that we can listen twice as much as we speak.",
          "Epictetus", "attributed", themes=["wisdom", "humor"], tone="wry"),
    entry("Circumstances don't make the man; they only reveal him to himself.",
          "Epictetus", "Discourses", themes=["wisdom", "perseverance"]),
    entry("If you want to improve, be content to be thought foolish and stupid.",
          "Epictetus", "Enchiridion", themes=["wisdom", "humility"]),

    # ---- Seneca (Letters from a Stoic, multiple PD translations) ----
    entry("It is not that we have a short time to live, but that we waste much of it.",
          "Seneca", "On the Shortness of Life", themes=["wisdom", "time"]),
    entry("Sometimes even to live is an act of courage.",
          "Seneca", "Letters from a Stoic", themes=["courage", "perseverance"], tone="uplifting"),
    entry("Difficulties strengthen the mind, as labor does the body.",
          "Seneca", "attributed", themes=["perseverance", "work"], tone="uplifting"),
    entry("Luck is what happens when preparation meets opportunity.",
          "Seneca", "attributed", themes=["wisdom", "work"]),
    entry("If a man knows not which port he sails, no wind is favorable.",
          "Seneca", "Letters from a Stoic", themes=["wisdom"]),
    entry("We suffer more often in imagination than in reality.",
          "Seneca", "Letters from a Stoic", themes=["wisdom"], tone="wry"),
    entry("As long as you live, keep learning how to live.",
          "Seneca", "Letters from a Stoic", themes=["wisdom"], tone="uplifting"),
    entry("It is the power of the mind to be unconquerable.",
          "Seneca", "Letters from a Stoic", themes=["courage", "perseverance"], tone="uplifting"),

    # ---- Hippocrates ----
    entry("Wherever the art of medicine is loved, there is also a love of humanity.",
          "Hippocrates", "Precepts", themes=["kindness", "love"], tone="uplifting", observances=["doctors-day"]),
    entry("Life is short, the art long, opportunity fleeting, experience treacherous, judgment difficult.",
          "Hippocrates", "Aphorisms I.1", themes=["wisdom", "time"], observances=["doctors-day"]),
    entry("Healing is a matter of time, but it is sometimes also a matter of opportunity.",
          "Hippocrates", "Precepts", themes=["wisdom", "time"], observances=["doctors-day"]),
    entry("Cure sometimes, treat often, comfort always.",
          "Hippocrates", "attributed", themes=["kindness"], tone="warm", observances=["doctors-day", "nurses-week"]),
    entry("Make a habit of two things: to help; or at least to do no harm.",
          "Hippocrates", "Epidemics, Book I", themes=["kindness", "wisdom"], observances=["doctors-day"]),
    entry("Walking is a man's best medicine.",
          "Hippocrates", "attributed", themes=["wisdom"], tone="warm"),
    entry("Natural forces within us are the true healers of disease.",
          "Hippocrates", "attributed", themes=["wisdom", "nature"]),

    # ---- William Osler (Aequanimitas, Counsels and Ideals) ----
    entry("The good physician treats the disease; the great physician treats the patient who has the disease.",
          "William Osler", "attributed", themes=["kindness", "wisdom"], tone="uplifting", observances=["doctors-day"]),
    entry("Listen to your patient, he is telling you the diagnosis.",
          "William Osler", "attributed", themes=["wisdom"], observances=["doctors-day"]),
    entry("The trained nurse has become one of the greatest blessings of humanity.",
          "William Osler", "Aequanimitas", themes=["kindness"], tone="uplifting", observances=["nurses-week"]),
    entry("To study the phenomena of disease without books is to sail an uncharted sea; while to study books without patients is not to go to sea at all.",
          "William Osler", "Aequanimitas", themes=["wisdom", "work"], observances=["doctors-day"]),
    entry("The whole art of medicine is in observation.",
          "William Osler", "attributed", themes=["wisdom", "work"], observances=["doctors-day"]),
    entry("The greater the ignorance, the greater the dogmatism.",
          "William Osler", "Aequanimitas", themes=["wisdom"], tone="wry"),
    entry("Do the kind thing and do it first.",
          "William Osler", "attributed", themes=["kindness"], tone="uplifting"),
    entry("Look wise, say nothing, and grunt. Speech was given to conceal thought.",
          "William Osler", "attributed", themes=["humor", "wisdom"], tone="wry"),

    # ---- Lincoln ----
    entry("Whatever you are, be a good one.",
          "Abraham Lincoln", "attributed", themes=["wisdom", "work"], tone="uplifting"),
    entry("I am a slow walker, but I never walk back.",
          "Abraham Lincoln", "Letter to Joshua Speed", themes=["perseverance"], tone="uplifting"),
    entry("The best thing about the future is that it comes one day at a time.",
          "Abraham Lincoln", "attributed", themes=["wisdom", "time", "hope"], tone="uplifting"),
    entry("Nearly all men can stand adversity, but if you want to test a man's character, give him power.",
          "Abraham Lincoln", "attributed", themes=["wisdom", "courage"]),
    entry("Folks are usually about as happy as they make their minds up to be.",
          "Abraham Lincoln", "attributed", themes=["wisdom", "humor"], tone="warm"),
    entry("It is not the years in your life that count. It's the life in your years.",
          "Abraham Lincoln", "attributed", themes=["wisdom", "time", "hope"], tone="uplifting"),
    entry("Most people are about as happy as they make up their minds to be.",
          "Abraham Lincoln", "attributed", themes=["wisdom"]),
    entry("Things may come to those who wait, but only the things left by those who hustle.",
          "Abraham Lincoln", "attributed", themes=["work", "perseverance"], tone="wry"),

    # ---- Wilde ----
    entry("Be yourself; everyone else is already taken.",
          "Oscar Wilde", "attributed", themes=["wisdom", "humor"], tone="wry"),
    entry("Experience is the name everyone gives to their mistakes.",
          "Oscar Wilde", "Lady Windermere's Fan", themes=["humor", "wisdom"], tone="wry"),
    entry("I can resist anything except temptation.",
          "Oscar Wilde", "Lady Windermere's Fan", themes=["humor"], tone="wry"),
    entry("Some cause happiness wherever they go; others, whenever they go.",
          "Oscar Wilde", "attributed", themes=["humor"], tone="wry"),
    entry("The truth is rarely pure and never simple.",
          "Oscar Wilde", "The Importance of Being Earnest", themes=["wisdom", "humor"], tone="wry"),
    entry("Always forgive your enemies; nothing annoys them so much.",
          "Oscar Wilde", "attributed", themes=["humor", "kindness"], tone="wry"),
    entry("Anyone who lives within their means suffers from a lack of imagination.",
          "Oscar Wilde", "attributed", themes=["humor"], tone="wry"),
    entry("Education is an admirable thing, but it is well to remember from time to time that nothing that is worth knowing can be taught.",
          "Oscar Wilde", "The Critic as Artist", themes=["wisdom", "humor"], tone="wry"),

    # ---- Mark Twain — selected (Pudd'nhead epigraphs handled by extractor below) ----
    entry("The two most important days in your life are the day you are born and the day you find out why.",
          "Mark Twain", "attributed", themes=["wisdom", "hope"], tone="uplifting"),
    entry("The secret of getting ahead is getting started.",
          "Mark Twain", "attributed", themes=["work", "perseverance"], tone="uplifting"),
    entry("Twenty years from now you will be more disappointed by the things that you didn't do than by the ones you did do.",
          "Mark Twain", "attributed", themes=["wisdom", "hope"], tone="uplifting"),
    entry("Kindness is the language which the deaf can hear and the blind can see.",
          "Mark Twain", "attributed", themes=["kindness"], tone="warm"),
    entry("If you tell the truth, you don't have to remember anything.",
          "Mark Twain", "attributed", themes=["wisdom", "humor"], tone="wry"),

    # ---- Misc literary/philosophical ----
    entry("The mass of men lead lives of quiet desperation.",
          "Henry David Thoreau", "Walden", themes=["wisdom"]),
    entry("Go confidently in the direction of your dreams. Live the life you have imagined.",
          "Henry David Thoreau", "Walden", themes=["hope", "courage"], tone="uplifting"),
    entry("Not all those who wander are lost.",
          "J.R.R. Tolkien", "The Fellowship of the Ring", themes=["wisdom", "hope"], tone="uplifting"),
    entry("In the midst of winter, I found there was, within me, an invincible summer.",
          "Albert Camus", "attributed", themes=["perseverance", "courage", "hope"], tone="uplifting", seasons=["winter"]),
    entry("Anyone who has never made a mistake has never tried anything new.",
          "Albert Einstein", "attributed", themes=["wisdom", "courage"], tone="uplifting"),
    entry("Try not to become a person of success, but rather try to become a person of value.",
          "Albert Einstein", "attributed", themes=["wisdom", "work"], tone="uplifting"),
    entry("Imagination is more important than knowledge.",
          "Albert Einstein", "On Science", themes=["wisdom"], tone="uplifting"),
    entry("That which does not kill us makes us stronger.",
          "Friedrich Nietzsche", "Twilight of the Idols", themes=["perseverance", "courage"], tone="uplifting"),
    entry("He who has a why to live for can bear almost any how.",
          "Friedrich Nietzsche", "Twilight of the Idols", themes=["perseverance", "hope"]),
    entry("The only way out is through.",
          "Robert Frost", "A Servant to Servants", themes=["perseverance"], tone="uplifting"),
    entry("In three words I can sum up everything I've learned about life: it goes on.",
          "Robert Frost", "attributed", themes=["wisdom", "perseverance"], tone="warm"),
    entry("Life can only be understood backwards; but it must be lived forwards.",
          "Søren Kierkegaard", "Journals", themes=["wisdom", "time"]),
    entry("Do not pray for an easy life. Pray for the strength to endure a difficult one.",
          "Bruce Lee", "attributed", themes=["perseverance", "courage"], tone="uplifting"),
    entry("If you want to lift yourself up, lift up someone else.",
          "Booker T. Washington", "Up from Slavery", themes=["kindness"], tone="uplifting"),
    entry("It always seems impossible until it's done.",
          "Nelson Mandela", "attributed", themes=["perseverance", "courage"], tone="uplifting"),
    entry("Be kind, for everyone you meet is fighting a hard battle.",
          "Ian Maclaren", "attributed", themes=["kindness"], tone="warm"),
    entry("Tell me, what is it you plan to do with your one wild and precious life?",
          "Mary Oliver", "The Summer Day", themes=["wisdom", "hope"], tone="uplifting"),
    entry("The world breaks everyone, and afterward, some are strong at the broken places.",
          "Ernest Hemingway", "A Farewell to Arms", themes=["perseverance", "courage"]),
    entry("Out of clutter, find simplicity. From discord, find harmony. In the middle of difficulty lies opportunity.",
          "Albert Einstein", "attributed", themes=["wisdom", "perseverance"], tone="uplifting"),
    entry("First, do no harm.",
          "Hippocratic tradition", "attributed", themes=["kindness", "wisdom"], observances=["doctors-day"]),

    # ---- Seasonal / observance specific ----
    entry("April is the cruelest month, breeding lilacs out of the dead land.",
          "T.S. Eliot", "The Waste Land", themes=["beauty"], seasons=["spring"]),
    entry("Spring is the time of year when it is summer in the sun and winter in the shade.",
          "Charles Dickens", "Great Expectations", themes=["humor", "nature"], seasons=["spring"], tone="wry"),
    entry("Autumn is a second spring when every leaf is a flower.",
          "Albert Camus", "attributed", themes=["beauty", "nature"], seasons=["autumn"], tone="uplifting"),
    entry("People don't notice whether it's winter or summer when they're happy.",
          "Anton Chekhov", "Three Sisters", themes=["wisdom", "hope"]),
    entry("In the depth of winter, I finally learned that within me there lay an invincible summer.",
          "Albert Camus", "Return to Tipasa", themes=["perseverance", "hope"], seasons=["winter"], tone="uplifting"),
    entry("Adopt the pace of nature: her secret is patience.",
          "Ralph Waldo Emerson", "attributed", themes=["wisdom", "nature"], tone="warm"),

    # ---- Communication / team-oriented (resonates for a clinic team) ----
    entry("The single biggest problem in communication is the illusion that it has taken place.",
          "George Bernard Shaw", "attributed", themes=["wisdom", "humor"], tone="wry"),
    entry("Alone we can do so little; together we can do so much.",
          "Helen Keller", "attributed", themes=["friendship", "work"], tone="uplifting"),
    entry("Coming together is a beginning. Keeping together is progress. Working together is success.",
          "Henry Ford", "attributed", themes=["work", "friendship"], tone="uplifting"),
    entry("If you want to go fast, go alone. If you want to go far, go together.",
          "African proverb", "traditional", themes=["friendship", "wisdom"], tone="uplifting"),
    entry("Talent wins games, but teamwork and intelligence win championships.",
          "Michael Jordan", "attributed", themes=["work", "friendship"], tone="uplifting"),
    entry("In union there is strength.",
          "Aesop", "Fables", themes=["friendship", "courage"], tone="uplifting"),

    # ---- Holidays / observances ----
    entry("Gratitude turns what we have into enough.",
          "Aesop", "attributed", themes=["wisdom"], tone="warm", observances=["thanksgiving"]),
    entry("Mothers hold their children's hands for a short while, but their hearts forever.",
          "Anonymous", "traditional", themes=["love", "kindness"], tone="warm", observances=["mothers-day"]),
    entry("A father is neither an anchor to hold us back nor a sail to take us there, but a guiding light whose love shows us the way.",
          "Anonymous", "traditional", themes=["love", "kindness"], tone="warm", observances=["fathers-day"]),
    entry("Freedom is never more than one generation away from extinction.",
          "Ronald Reagan", "Address to the Phoenix Chamber of Commerce, 1961", themes=["freedom"], observances=["independence-day"]),

    # ---- Humility, work ethic, professional ----
    entry("Genius is one percent inspiration and ninety-nine percent perspiration.",
          "Thomas Edison", "attributed", themes=["work", "perseverance"]),
    entry("It is hard to fail, but it is worse never to have tried to succeed.",
          "Theodore Roosevelt", "Strenuous Life Speech", themes=["courage", "perseverance"], tone="uplifting"),
    entry("Do what you can, with what you have, where you are.",
          "Theodore Roosevelt", "Autobiography", themes=["work", "perseverance"], tone="uplifting"),
    entry("Comparison is the thief of joy.",
          "Theodore Roosevelt", "attributed", themes=["wisdom"], tone="wry"),
    entry("Far and away the best prize that life offers is the chance to work hard at work worth doing.",
          "Theodore Roosevelt", "Labor Day Speech, 1903", themes=["work"], tone="uplifting", observances=["labor-day"]),

    # ---- Bierce — hand-picked from The Devil's Dictionary ----
    # (Skipping the dated, religious-mocking, ethnic, or gendered entries.
    # These are the timeless witty ones that still land.)
    entry("Habit, n. A shackle for the free.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Hurry, n. The dispatch of bunglers.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Advice, n. The smallest current coin.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Adage, n. Boned wisdom for weak teeth.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Accountability, n. The mother of caution.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Achievement, n. The death of endeavor and the birth of disgust.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "work"], tone="wry"),
    entry("Applause, n. The echo of a platitude.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Bore, n. A person who talks when you wish him to listen.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Patience, n. A minor form of despair, disguised as a virtue.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Politeness, n. The most acceptable hypocrisy.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Misfortune, n. The kind of fortune that never misses.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Hope, n. Desire and expectation rolled into one.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "hope"], tone="wry"),
    entry("Predicament, n. The wage of consistency.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Lecturer, n. One with his hand in your pocket, his tongue in your ear, and his faith in your patience.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Twice, adv. Once too often.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Year, n. A period of three hundred and sixty-five disappointments.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "time"], tone="wry"),
    entry("Acquaintance, n. A person whom we know well enough to borrow from, but not well enough to lend to.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "friendship"], tone="wry"),
    entry("Egotist, n. A person of low taste — more interested in himself than in me.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Future, n. That period of time in which our affairs prosper, our friends are true, and our happiness is assured.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "time"], tone="wry"),
    entry("Distress, n. A disease incurred by exposure to the prosperity of a friend.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Telephone, n. An invention of the devil which abrogates some of the advantages of making a disagreeable person keep his distance.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Saint, n. A dead sinner revised and edited.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Education, n. That which discloses to the wise and disguises from the foolish their lack of understanding.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Conservative, n. A statesman who is enamored of existing evils, as distinguished from the Liberal, who wishes to replace them with others.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Diplomacy, n. The patriotic art of lying for one's country.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Mausoleum, n. The final and funniest folly of the rich.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Idleness, n. A model farm where the devil experiments with seeds of new sins.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "work"], tone="wry"),
    entry("Optimist, n. A proponent of the doctrine that black is white.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "hope"], tone="wry"),
    entry("Pessimism, n. A philosophy forced upon the convictions of the observer by the disheartening prevalence of the optimist with his scarecrow hope and his unsightly smile.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Self-Evident, adj. Evident to one's self and to nobody else.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("More, n. The comparative degree of too much.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Enough, n. All there is in the world if you like it.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Pleasure, n. The least hateful form of dejection.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Fashion, n. A despot whom the wise ridicule and obey.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Quotation, n. The act of repeating erroneously the words of another.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Resolute, adj. Obstinate in a course that we approve.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor"], tone="wry"),
    entry("Cynic, n. A blackguard whose faulty vision sees things as they are, not as they ought to be.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "wisdom"], tone="wry"),
    entry("Friendship, n. A ship big enough to carry two in fair weather, but only one in foul.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "friendship"], tone="wry"),
    entry("Patient, adj. Bearing the offences of others with composure, while plotting our own.",
          "Ambrose Bierce", "The Devil's Dictionary", themes=["humor", "perseverance"], tone="wry"),
]


# ============================================================================
# Parsers for the PG source texts
# ============================================================================

def extract_bierce(text: str) -> list[dict]:
    """The Devil's Dictionary — keep short pithy definitions."""
    # Entries look like: WORD, n.  Definition (one paragraph).
    out = []
    blocklist = re.compile(
        r"\b(nigger|negro|jew|chinaman|coolie|hottentot|savage|squaw|injun|"
        r"papist|popish|barbarian)\w*\b|"
        r"\b(damn|hell|devil|satan|sin)\w*\b",
        re.IGNORECASE,
    )
    pattern = re.compile(
        r"^([A-Z][A-Z'-]+),\s+([a-z]+)\.\s+(.+?)(?=\n\n|\n[A-Z][A-Z]+,\s)",
        re.DOTALL | re.MULTILINE,
    )
    # Simpler line-based approach
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Z][A-Z'-]+),\s+[a-z]+\.\s+(.+)$", lines[i])
        if m:
            word = m.group(1)
            body = m.group(2)
            # consume continuation lines
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r"^[A-Z][A-Z'-]+,\s+[a-z]+\.", lines[j]):
                body += " " + lines[j].strip()
                j += 1
            i = j
            body = re.sub(r"\s+", " ", body).strip()
            # Filter: short and pithy
            if 20 <= len(body) <= 140 and "[" not in body:
                if blocklist.search(body) or blocklist.search(word):
                    continue
                # No verse / no poem markers
                if body.endswith(":") or body.count(",") > 4:
                    continue
                out.append(entry(
                    f'{word.title()}, n. {body}',
                    "Ambrose Bierce", "The Devil's Dictionary",
                    themes=["humor", "wisdom"], tone="wry",
                ))
        else:
            i += 1
    return out


def extract_twain_calendar(text: str) -> list[dict]:
    """Extract Pudd'nhead Wilson's Calendar epigraphs — chapter headers."""
    out = []
    # Pattern: a paragraph followed by --Pudd'nhead Wilson's Calendar (with apostrophes)
    matches = re.findall(
        r"([^\n]+(?:\n[^\n]+){0,3})—Pudd[’']nhead Wilson[’']s (?:New )?Calendar",
        text,
    )
    # Try ASCII fallback
    if not matches:
        matches = re.findall(
            r"([^\n]+(?:\n[^\n]+){0,3})--Pudd[’']?nhead Wilson[’']?s (?:New )?Calendar",
            text,
        )
    seen = set()
    for m in matches:
        q = re.sub(r"\s+", " ", m).strip().lstrip("-").strip()
        if q.startswith("his ") or q.startswith("often "):
            # mid-sentence start — skip
            continue
        if len(q) < 30 or len(q) > 200:
            continue
        if q in seen:
            continue
        seen.add(q)
        out.append(entry(q, "Mark Twain", "Pudd'nhead Wilson's Calendar",
                         themes=["humor", "wisdom"], tone="wry"))
    return out


def load_seeds() -> list[dict]:
    """Carry over the original 53 hand-curated seeds from clinic-task-tracker."""
    if not SEED.exists():
        return []
    raw = json.loads(SEED.read_text())
    out = []
    seed_re = re.compile(r'^"(.+?)"\s*—\s*(.+?)(?:,\s*(.+))?$')
    for line in raw:
        m = seed_re.match(line.strip())
        if not m:
            continue
        out.append(entry(
            m.group(1),
            m.group(2).strip(),
            (m.group(3) or "").strip(),
            tone="uplifting",
            themes=["wisdom"],
        ))
    return out


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("[curate] hand-curated entries:", len(HAND_CURATED))

    # Bierce — hand-picked entries are in HAND_CURATED. Skip the bulk auto-extractor;
    # most of the 884 dictionary entries are dated, religious-mocking, ethnic, or
    # otherwise off-tone for a clinic email.

    twain_text = (RAW / "twain-puddnhead.txt").read_text()
    twain_entries = extract_twain_calendar(twain_text)
    print("[curate] twain calendar auto-extracted:", len(twain_entries))

    seed_entries = load_seeds()
    print("[curate] seed quotes carried over:", len(seed_entries))

    all_entries = HAND_CURATED + twain_entries + seed_entries

    # Dedupe by quote text
    seen = set()
    deduped = []
    for e in all_entries:
        key = e["quote"][:60].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    # Assign sequential IDs
    for i, e in enumerate(deduped, start=1):
        e["id"] = f"curated-{i:04d}"

    print(f"[curate] total after dedupe: {len(deduped)}")
    print()
    print("[sample — 10 random]")
    import random
    rng = random.Random(42)
    for e in rng.sample(deduped, k=min(10, len(deduped))):
        print(f"  [{e['tone']:9}] {e['quote'][:100]} — {e['author']}")

    OUT.write_text(json.dumps(deduped, ensure_ascii=False, indent=2) + "\n")
    print(f"\n[curate] wrote {len(deduped)} entries to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
