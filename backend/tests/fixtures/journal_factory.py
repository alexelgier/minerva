"""
Factory for creating realistic journal entries based on actual usage patterns.

This factory generates test data that closely mirrors the structure and content
of real journal entries from the Minerva system.
"""

import re
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from minerva_backend.graph.models.documents import JournalEntry


class JournalEntryFactory:
    """Factory for creating realistic journal entries for testing."""
    
    # Sample journal content patterns based on real entries
    SAMPLE_ENTRIES = [
        {
            "date": "2025-09-15",
            "content": """[[2025]] [[2025-09]] [[2025-09-15]]  Monday
Programé [[Minerva]] todo el dia, y me fui a dormir 22hs

---
## Sleep
Wake time: 
Bedtime: 2200

---
# 📝 Daily Wellbeing Check-in

## PANAS
Rate each 1–5 (1 = very slightly, 5 = extremely)

**Positive Affect**
- Interested:: 0
- Excited:: 0
- Strong:: 0
- Enthusiastic:: 0
- Proud:: 0
- Alert:: 0
- Inspired:: 0
- Determined:: 0
- Attentive:: 0
- Active:: 0

**Negative Affect**
- Distressed:: 0
- Upset:: 0
- Guilty:: 0
- Scared:: 0
- Hostile:: 0
- Irritable:: 0
- Ashamed:: 0
- Nervous:: 0
- Jittery:: 0
- Afraid:: 0

---

## ## BPNS (Basic Psychological Needs)
Rate each 1–7 

**Autonomy**
- I feel like I can make choices about the things I do:: 0
- I feel free to decide how I do my daily tasks:: 0

**Competence**
- I feel capable at the things I do:: 0
- I can successfully complete challenging tasks:: 0

**Relatedness**
- I feel close and connected with the people around me:: 0
- I get along well with the people I interact with daily:: 0
- I feel supported by others in my life:: 0

---

## Flourishing Scale
Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)

- I lead a purposeful and meaningful life:: 0
- My social relationships are supportive and rewarding:: 0
- I am engaged and interested in my daily activities:: 0
- I actively contribute to the happiness and well-being of others:: 0
- I am competent and capable in the activities that are important to me:: 0
- I am a good person and live a good life:: 0
- I am optimistic about my future:: 0
- People respect me:: 0"""
        },
        {
            "date": "2025-09-14",
            "content": """[[2025]] [[2025-09]] [[2025-09-14]]  Sunday

1430, Desperté con la ayuda de [[Ana Sorin|Ana]], muy amorosa. 

Me fui al [[patio]] a tomar [[Mate]] y ver un poco el [[Celular]].

1915 hay que resolver la [[Comida]], me voy a cruzar al [[Chino]].

Estoy cocinando [[Dip de Morrón Asado]].

2200 [[Cena]] con [[Ana Sorin|Ana]]. [[Dip de Morrón Asado]], [[Nachos]], [[Milanesa de Soja|Suelas]], [[Ensalada]]. Vimos un poco de un documental de [[Elefante]]. 

[[Ana Sorin|Ana]] se fue a trabajar, yo a [[Minerva]]. 

0800 sigo con [[Minerva]]. Llegue a hacer inferencia! Funciona el pipeline y estoy extrayendo personas. Que alegria! Lloré de la alegría cuando salió la primer inferencia. Estuve muchas horas tratando de hacer funcionar [[temporal.io]]. A veces las librerias complican mas que ayudar. Pero una vez que funcionan, sirven. Es lindo el dashboard que tiene.

[[Ana Sorin|Ana]] se despertó, se hizo [[Mate Cocido]], yo un [[Té]].

No tengo sueño. Que hago? Sigo de largo? Voy a intentar seguir de largo. Siesta si hace falta, pero dormirme a un horario razonable, no puedo dormirme a las 0900 y despertar todo hecho mierda a las 1400, no sirve. Sigo de largo. 

---
## Sleep
Wake time: 1430
Bedtime: 

---
# 📝 Daily Wellbeing Check-in

## PANAS
Rate each 1–5 (1 = very slightly, 5 = extremely)

**Positive Affect**
- Interested:: 4
- Excited:: 5
- Strong:: 3
- Enthusiastic:: 4
- Proud:: 5
- Alert:: 3
- Inspired:: 2
- Determined:: 4
- Attentive:: 3
- Active:: 4

**Negative Affect**
- Distressed:: 1
- Upset:: 1
- Guilty:: 1
- Scared:: 1
- Hostile:: 1
- Irritable:: 1
- Ashamed:: 2
- Nervous:: 2
- Jittery:: 1
- Afraid:: 2

---

## ## BPNS (Basic Psychological Needs)
Rate each 1–7 

**Autonomy**
- I feel like I can make choices about the things I do:: 7
- I feel free to decide how I do my daily tasks:: 7

**Competence**
- I feel capable at the things I do:: 7
- I can successfully complete challenging tasks:: 7

**Relatedness**
- I feel close and connected with the people around me:: 4
- I get along well with the people I interact with daily:: 5
- I feel supported by others in my life:: 2

---

## Flourishing Scale
Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)

- I lead a purposeful and meaningful life:: 3
- My social relationships are supportive and rewarding:: 2
- I am engaged and interested in my daily activities:: 7
- I actively contribute to the happiness and well-being of others:: 5
- I am competent and capable in the activities that are important to me:: 7
- I am a good person and live a good life:: 4
- I am optimistic about my future:: 3
- People respect me:: 3"""
        }
    ]
    
    @classmethod
    def create_journal_entry(
        cls,
        date_str: str = "2025-09-15",
        content: Optional[str] = None,
        panas_pos: Optional[List[int]] = None,
        panas_neg: Optional[List[int]] = None,
        bpns: Optional[List[int]] = None,
        flourishing: Optional[List[int]] = None,
        wake_time: Optional[str] = None,
        bedtime: Optional[str] = None
    ) -> JournalEntry:
        """
        Create a journal entry with realistic data.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            content: Custom content, if None uses sample content
            panas_pos: PANAS positive scores (10 values)
            panas_neg: PANAS negative scores (10 values)
            bpns: BPNS scores (7 values)
            flourishing: Flourishing scores (8 values)
            wake_time: Wake time in HHMM format
            bedtime: Bedtime in HHMM format
        """
        if content is None:
            # Find sample content for the date or use first one
            sample = next(
                (s for s in cls.SAMPLE_ENTRIES if s["date"] == date_str),
                cls.SAMPLE_ENTRIES[0]
            )
            content = sample["content"]
        
        return JournalEntry.from_text(content, date_str)
    
    @classmethod
    def create_minimal_journal_entry(
        cls,
        date_str: str = "2025-09-15",
        text: str = "Hoy trabajé en [[Minerva]] todo el día."
    ) -> JournalEntry:
        """Create a minimal journal entry for simple tests."""
        content = f"""[[{date_str[:4]}]] [[{date_str[:7]}]] [[{date_str}]]  Monday
{text}

---
## Sleep
Wake time: 
Bedtime: 

---
# 📝 Daily Wellbeing Check-in

## PANAS
Rate each 1–5 (1 = very slightly, 5 = extremely)

**Positive Affect**
- Interested:: 0
- Excited:: 0
- Strong:: 0
- Enthusiastic:: 0
- Proud:: 0
- Alert:: 0
- Inspired:: 0
- Determined:: 0
- Attentive:: 0
- Active:: 0

**Negative Affect**
- Distressed:: 0
- Upset:: 0
- Guilty:: 0
- Scared:: 0
- Hostile:: 0
- Irritable:: 0
- Ashamed:: 0
- Nervous:: 0
- Jittery:: 0
- Afraid:: 0

---

## ## BPNS (Basic Psychological Needs)
Rate each 1–7 

**Autonomy**
- I feel like I can make choices about the things I do:: 0
- I feel free to decide how I do my daily tasks:: 0

**Competence**
- I feel capable at the things I do:: 0
- I can successfully complete challenging tasks:: 0

**Relatedness**
- I feel close and connected with the people around me:: 0
- I get along well with the people I interact with daily:: 0
- I feel supported by others in my life:: 0

---

## Flourishing Scale
Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)

- I lead a purposeful and meaningful life:: 0
- My social relationships are supportive and rewarding:: 0
- I am engaged and interested in my daily activities:: 0
- I actively contribute to the happiness and well-being of others:: 0
- I am competent and capable in the activities that are important to me:: 0
- I am a good person and live a good life:: 0
- I am optimistic about my future:: 0
- People respect me:: 0"""
        
        return JournalEntry.from_text(content, date_str)
    
    @classmethod
    def create_journal_with_entities(
        cls,
        date_str: str = "2025-09-15",
        entities: List[str] = None
    ) -> JournalEntry:
        """Create a journal entry with specific entities mentioned."""
        if entities is None:
            entities = ["[[Minerva]]", "[[Ana Sorin|Ana]]", "[[patio]]"]
        
        text = f"Hoy trabajé en {' '.join(entities)} todo el día."
        return cls.create_minimal_journal_entry(date_str, text)
    
    @classmethod
    def get_sample_entities_from_journals(cls) -> List[str]:
        """Extract all unique entities mentioned in sample journals."""
        entities = set()
        for sample in cls.SAMPLE_ENTRIES:
            # Find all [[entity]] patterns
            matches = re.findall(r'\[\[([^\]]+)\]\]', sample["content"])
            entities.update(matches)
        return sorted(list(entities))
