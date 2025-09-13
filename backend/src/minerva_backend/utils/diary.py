import datetime
import re
from typing import Any

from minerva_backend.graph.model import JournalEntry


def parse_diary_entry(text: str, date: str) -> JournalEntry:
    """Parse diary entry and return a JournalEntry object."""
    diary_entry = {}

    # PANAS Positive
    panas_pos_match = re.search(
        r"## PANAS.*?Positive Affect.*?"
        r"Interested::\s*(\d+).*?"
        r"Excited::\s*(\d+).*?"
        r"Strong::\s*(\d+).*?"
        r"Enthusiastic::\s*(\d+).*?"
        r"Proud::\s*(\d+).*?"
        r"Alert::\s*(\d+).*?"
        r"Inspired::\s*(\d+).*?"
        r"Determined::\s*(\d+).*?"
        r"Attentive::\s*(\d+).*?"
        r"Active::\s*(\d+)",
        text, re.DOTALL)
    if panas_pos_match:
        diary_entry['panas_pos'] = [int(val) for val in panas_pos_match.groups()]

    # PANAS Negative
    panas_neg_match = re.search(
        r"Negative Affect.*?"
        r"Distressed::\s*(\d+).*?"
        r"Upset::\s*(\d+).*?"
        r"Guilty::\s*(\d+).*?"
        r"Scared::\s*(\d+).*?"
        r"Hostile::\s*(\d+).*?"
        r"Irritable::\s*(\d+).*?"
        r"Ashamed::\s*(\d+).*?"
        r"Nervous::\s*(\d+).*?"
        r"Jittery::\s*(\d+).*?"
        r"Afraid::\s*(\d+)",
        text, re.DOTALL)
    if panas_neg_match:
        diary_entry['panas_neg'] = [int(val) for val in panas_neg_match.groups()]

    # BPNS
    bpns_match = re.search(
        r"## BPNS.*?"
        r"Autonomy.*?"
        r"I feel like I can make choices about the things I do::\s*(\d+).*?"
        r"I feel free to decide how I do my daily tasks::\s*(\d+).*?"
        r"Competence.*?"
        r"I feel capable at the things I do::\s*(\d+).*?"
        r"I can successfully complete challenging tasks::\s*(\d+).*?"
        r"Relatedness.*?"
        r"I feel close and connected with the people around me::"
        r"\s*(\d+).*?I get along well with the people I interact with daily::"
        r"\s*(\d+).*?I feel supported by others in my life::\s*(\d+)",
        text, re.DOTALL)
    if bpns_match:
        diary_entry['bpns'] = [int(val) for val in bpns_match.groups()]

    # Flourishing
    flour_match = re.search(
        r"## Flourishing Scale.*?I lead a purposeful and meaningful life::\s*(\d+).*?"
        r"My social relationships are supportive and rewarding::\s*(\d+).*?"
        r"I am engaged and interested in my daily activities::\s*(\d+).*?"
        r"I actively contribute to the happiness and well-being of others::\s*(\d+).*?"
        r"I am competent and capable in the activities that are important to me::\s*(\d+).*?"
        r"I am a good person and live a good life::\s*(\d+).*?"
        r"I am optimistic about my future::\s*(\d+).*?"
        r"People respect me::\s*(\d+)",
        text, re.DOTALL)
    if flour_match:
        diary_entry['flourishing'] = [int(val) for val in flour_match.groups()]

    # Wake / Bed
    wake_bed_match = re.search(
        r"Wake time:\s*(\d\d:?\d\d).*?Bedtime:\s*(\d\d:?\d\d)",
        text, re.DOTALL)
    if wake_bed_match:
        wake = "".join(wake_bed_match.groups()[0].split(":"))
        bed = "".join(wake_bed_match.groups()[1].split(":"))
        diary_entry['wake'] = datetime.time(int(wake[:2]), int(wake[2:]))
        diary_entry['sleep'] = datetime.time(int(bed[:2]), int(bed[2:]))

    # Date
    date = date.split("-")
    diary_entry['date'] = datetime.date(int(date[0]), int(date[1]), int(date[2]))

    # Narration
    diary_entry['text'] = re.search(r"(.+?)(?=\n*---\n*-\s*Imagen, Detalle:|\n*---.*## Noticias|\n*---.*## Sleep)",
                                    text, re.DOTALL).group(0)

    return JournalEntry(
        id=date,
        date=diary_entry['date'],
        text=diary_entry['text'],
        fulltext=text,
        panas_pos=diary_entry.get('panas_pos'),
        panas_neg=diary_entry.get('panas_neg'),
        bpns=diary_entry.get('bpns'),
        flourishing=diary_entry.get('flourishing'),
        wake=diary_entry.get('wake'),
        sleep=diary_entry.get('sleep'),
    )
