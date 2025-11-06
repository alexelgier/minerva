import asyncio
from neo4j_graphrag.experimental.components.schema import SchemaFromTextExtractor

import os

from langchain_google_genai import ChatGoogleGenerativeAI



async def main():
    # Instantiate the automatic schema extractor component
    schema_extractor = SchemaFromTextExtractor(
        llm=ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                temperature=0.3  # Some creativity for analysis
            )
    )
    # Extract the schema from the text
    extracted_schema = await schema_extractor.run(text="""Desperte 1530
Bajé, me preparé [[Mate]]. 

[[Ana Sorin|Ana]] vino y se sentó conmigo en el [[patio]]. Estuvimos un ratito charlando, no salio tan bien, empezamos amables, nos abrazamos. Yo recorde que anoche me acusaba de estar intentanto que se suicde y me largue a llorar. Le dije que suficiente abrazo y ella dijo que mejor dormia afuera hoy. Ahi medio nos cruzamos, yo no me lo tome bien de su parte. Nos fuimos cada uno a ver a su madre por el [[Día de la Madre]].

En lo de [[Michelle Elgier|Michelle]] estuvo muy lindo, jugue un largo rato con [[Rafi]], [[Eloy Goldfrid]], y [[Teo]]. Charle un rato sobre [[Ana Sorin|Ana]] con [[Michelle Elgier|Michelle]] y [[Roxana L'arco]].

Cuando volvi a casa charlamos un rato mas con [[Ana Sorin|Ana]], dificil, pero conciliador. Le pedi que trate de bajar el tono, se aferra a lecturas muy tremendas propias de la pelea y no desescala. 

Despues me quedé largo rato trabajando en [[Secuaz]] y viendo [[Mandalorian]]. 

0411 [[journaling|Escribir ésto]]. 

Mañana tengo que despertar temprano para ayudar a [[Martin Alvarez Heymann|Martin]] a mudarse. """)
    return extracted_schema

if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        print("[main] Setting GOOGLE_API_KEY environment variable")
        os.environ["GOOGLE_API_KEY"] = "AIzaSyCw3FzCBecZscg1bh5auhEtkMWLzg3wDTs"
    result = asyncio.run(main())
    for r in result:
        print(r)