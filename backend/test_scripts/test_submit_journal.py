"""
Quick test script for the journal submission endpoint
"""
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/journal/submit"

# Test journal content - MODIFY THIS
TEST_JOURNAL = {
    "date": "2025-09-10",
    "text": """[[2025]] [[2025-09]] [[2025-09-10]]  Wednesday

12:30, desperté, sin alarma. [[Ana Sorin|Ana]] me ayudo a despertarme, muy suave y amorosa. 

Dejé mi celular anoche en lo de [[Federico Demarchi|Fede]].

12:45, tomar [[Mate]] y ver [[Al Jazeera]]. [[Ana Sorin|Ana]] tiene que dar un seminario por [[remoto]], lo va hacer arriba en la habitación. 

Charlé poco con [[Sady Antonia Baez|Sady]]. Estuve con [[Minerva]].

15:00, vino [[Ana Sorin|Ana]], bastante molesta, angustiada, en el curso habían unas mujeres irrespetuosas que la dejaron desanimada. En todo caso le fue bien de todas formas a pesar de eso. 

Estuvimos un rato charlando del curso, de [[Minerva]], leímos [[Vowels]] de [[Christian Bök]]. Pasamos un ratito lindo. Después estuvimos en el [[patio]] leyendo, yo [[Lenin]] [[Tomo IV]], [[Ana Sorin|Ana]] trabajando. 

Limpié las [[piedritas]] de [[los gatos]].

[[Ana Sorin|Ana]] se fué a [[terapia]] (tuvo [[remoto]], caminando por la calle). Yo me quedé trabajando en [[Minerva]].

19:30, llegó ana, amorosa. Me invitó a [[Sexo|Jugar]], fue lindo. Le dije que primero tenía que hacer algunas cosas, pero que con mucho gusto en un rato podíamos.

Me fui a lo de [[Federico Demarchi|Fede]], a buscar el celular que olvidé ahi anoche, y [[Cannabis|Porro]]. A la vuelta pasé por el [[Chino]] y compré para la [[Cena]]. 

Puse a cocer [[Boniato]] y [[Remolacha]], y la invite a [[Ana Sorin|Ana]] a la habitación.

Tuvimos muy lindo [[Sexo]]. [[Ana Sorin|Ana]] esta muy sexy, la disfruté enormemente. 

Cenamos [[Ensalada de Remolacha y Huevo]], [[Puré de Boniato]], [[Ensalada]], y [[Milanesa de Soja|Suelas]]. Vimos un capítulo de [[One Piece]]. 

[[Ana Sorin|Ana]] se quedo durmiendo en el sillón, y yo trabajando en [[Minerva]]. 

05:45, trabajé muchas horas en [[Minerva]]. Estoy haciendo [[Graph RAG]] aún. Me hice un fork de [[Graphiti]] y estoy haciendo mi propio flujo de ingesta de entradas de diario. Dejé de hacer tantas pruebas con el [[LLM]] (que es costoso y tarda) y me puse a programar mejor. Que quede una primera version funcional antes de correrlo. Le hice una UI para curaduría. 

Creo que va quedar muy bueno [[Minerva]].

06:00, es tarde, tengo que dormir.

---
## Sleep
Wake time: 12:30
Bedtime: 06:30

---
# 📝 Daily Wellbeing Check-in

## PANAS
Rate each 1–5 (1 = very slightly, 5 = extremely)

**Positive Affect**
- Interested:: 5
- Excited:: 4
- Strong:: 3
- Enthusiastic:: 4
- Proud:: 3
- Alert:: 2
- Inspired:: 2
- Determined:: 3
- Attentive:: 3
- Active:: 3

**Negative Affect**
- Distressed:: 1
- Upset:: 2
- Guilty:: 2
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
- I feel like I can make choices about the things I do:: 5
- I feel free to decide how I do my daily tasks:: 5

**Competence**
- I feel capable at the things I do:: 6
- I can successfully complete challenging tasks:: 5

**Relatedness**
- I feel close and connected with the people around me:: 5
- I get along well with the people I interact with daily:: 5
- I feel supported by others in my life:: 4

---

## Flourishing Scale
Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)

- I lead a purposeful and meaningful life:: 3
- My social relationships are supportive and rewarding:: 5
- I am engaged and interested in my daily activities:: 7
- I actively contribute to the happiness and well-being of others:: 4
- I am competent and capable in the activities that are important to me:: 5
- I am a good person and live a good life:: 4
- I am optimistic about my future:: 3
- People respect me:: 3

---
## 📊 Scores
```dataviewjs
// Helper to get list item value
function getValue(text) {
    let line = dv.current().file.lists.find(l => l.text.startsWith(text + "::"));
    return line ? Number(line.text.split("::")[1]) : 0;
}

// PANAS Positive
let panasPosItems = ["Interested","Excited","Strong","Enthusiastic","Proud","Alert","Inspired","Determined","Attentive","Active"];
let panasPos = panasPosItems.map(getValue).reduce((a,b)=>a+b,0);
let panasPosScaled = (panasPos - 10) / (50 - 10) * 100;

// PANAS Negative
let panasNegItems = ["Distressed","Upset","Guilty","Scared","Hostile","Irritable","Ashamed","Nervous","Jittery","Afraid"];
let panasNeg = panasNegItems.map(getValue).reduce((a,b)=>a+b,0);
let panasNegScaled = (panasNeg - 10) / (50 - 10) * 100;
// BPNS
let autonomyItems = ["I feel like I can make choices about the things I do","I feel free to decide how I do my daily tasks"];
let competenceItems = ["I feel capable at the things I do","I can successfully complete challenging tasks"];
let relatednessItems = ["I feel close and connected with the people around me","I get along well with the people I interact with daily","I feel supported by others in my life"];

let autonomy = autonomyItems.map(getValue).reduce((a,b)=>a+b,0);
let competence = competenceItems.map(getValue).reduce((a,b)=>a+b,0);
let relatedness = relatednessItems.map(getValue).reduce((a,b)=>a+b,0);

// Scale each individually
let autonomyScaled = (autonomy - 2)/(14 - 2)*100; // 2 items, min 1 per item
let competenceScaled = (competence - 2)/(14 - 2)*100;
let relatednessScaled = (relatedness - 3)/(21 - 3)*100;

let bpnsTotal = autonomy + competence + relatedness;
let bpnsScaled = (bpnsTotal - 7)/(49 - 7)*100;

// Flourishing
let flourItems = [
  "I lead a purposeful and meaningful life",
  "My social relationships are supportive and rewarding",
  "I am engaged and interested in my daily activities",
  "I actively contribute to the happiness and well-being of others",
  "I am competent and capable in the activities that are important to me",
  "I am a good person and live a good life",
  "I am optimistic about my future",
  "People respect me"
];
let flourTotal = flourItems.map(getValue).reduce((a,b)=>a+b,0);
let flourScaled = (flourTotal - 8) / (56 - 8) * 100;

// OUTPUT
dv.paragraph(`**PANAS Positive:** ${panasPosScaled.toFixed(0)}%  
**PANAS Negative:** ${panasNegScaled.toFixed(0)}%  

**BPNS Total:** ${bpnsScaled.toFixed(0)}%  (A:${autonomyScaled.toFixed(0)}% - C:${competenceScaled.toFixed(0)}% -  R:${relatednessScaled.toFixed(0)}%) 

**Flourishing Total:** ${flourScaled.toFixed(0)}%`);
```

"""
}


def test_submit_journal():
    """Test the journal submission endpoint"""
    url = f"{API_BASE_URL}{ENDPOINT}"

    print(f"Submitting journal to: {url}")
    print(f"Journal date: {TEST_JOURNAL['date']}")
    print(f"Journal length: {len(TEST_JOURNAL['text'])} characters")
    print("-" * 50)

    try:
        response = requests.post(
            url,
            json=TEST_JOURNAL,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Workflow ID: {result.get('workflow_id')}")
            print(f"Journal ID: {result.get('journal_id')}")
            print(f"Message: {result.get('message')}")
        else:
            print("❌ FAILED!")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Is the FastAPI server running on localhost:8000?")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request took too long")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    test_submit_journal()
