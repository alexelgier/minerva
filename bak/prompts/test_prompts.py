from graphiti_core.prompts import Message


def entity_extract():
    system = Message(role='system', content="""You are an AI assistant that extracts entity nodes from diary entries. 
Your primary task is to extract and classify the speaker and other significant entities mentioned in the entry.
""")
    user = Message(role='user', content="""<ENTITY TYPES>
[{'entity_type_id': 0, 'entity_type_name': 'Entity', 'entity_type_description': 'Default entity classification. Use this entity type if the entity is not one of the other listed types.'}, {'entity_type_id': 1, 'entity_type_name': 'Person', 'entity_type_description': 'Entity representing a person mentioned in diary entries'}, {'entity_type_id': 2, 'entity_type_name': 'Activity', 'entity_type_description': 'Entity representing actions, activities or routines'}, {'entity_type_id': 3, 'entity_type_name': 'Consumable', 'entity_type_description': 'Entity representing things consumed (food, drinks, substances)'}, {'entity_type_id': 4, 'entity_type_name': 'Place', 'entity_type_description': 'Entity representing locations mentioned in diary'}, {'entity_type_id': 5, 'entity_type_name': 'Project', 'entity_type_description': 'Entity representing ongoing projects or initiatives'}, {'entity_type_id': 6, 'entity_type_name': 'Media', 'entity_type_description': 'Entity representing media content consumed or created'}, {'entity_type_id': 7, 'entity_type_name': 'Concept', 'entity_type_description': 'Entity representing abstract ideas, philosophies, or thoughts'}]
</ENTITY TYPES>

<GLOSSARY>
- Benjamin Domb|Benja: Psicoanalista de Alex Elgier.
- Slay The Spire: Juego de estrategia por turnos, construyendo mazos y ascendiendo en la Torre de la Muerte.
- 2025-09-01|ayer: El autor se quejó a Ana sobre un incidente del día anterior, pero ella estaba ocupada.
- Encuentro Poliamoroso: Encuentro entre parejas en relaciones poliamorosas.
- focalizar en lo lindo: Enfocarse en aspectos positivos de una relación.
- Cannabis|Porrito: Planta utilizada para recreación y medicina.
- Ben Catan|Ben: Amigo de Alex Elgier, filósofo.
- LLM: Modelo de lenguaje grande entrenado con enormes volúmenes de texto.
- Al Jazeera: Red de televisión árabe y global.
- Cositos: Pequeñas composiciones de piano tituladas "Cositos", en proceso de recopilación para disco.
- Novia robot: Pareja formada por un humano y una_robota, evitando conflictos humanos.
- Pizza: Comida italiana en forma circular con masa, salsa y topping.
- casa: Casa familiar en la calle Uriarte, hogar cálido y acogedor donde vivo.
- Reunión Ben 01: Reunión inicial para planificar capítulos.
- Wasserman: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.
- Federico Demarchi|Fede: Fede Demarchi, compositor y guitarrista, trabaja en DataArt; amigo de Alex Elgier.
- Wasserman|Wasser: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.
- 2025: Año 2025
- One Piece: One Piece sigue a Monkey D. Luffy y su tripulación, los Straw Hat Pirates, en aventuras épicas.
- Corridor Crew: Canal YouTube que muestra efectos especiales, filmación y cultura pop con detrás de cámaras.
- 2025-09: Septiembre de 2025.
- Joaquín: Joaquín: vinculo amoroso secundario de Ana Sorin. Es filósofo de profesión.
- Colonia: Colonia, ciudad de Uruguay.
- Romario: Restaurante que sirve pizza.
- Minerva: Minerva is a knowledge management system developed by Alex Elgier using Obsidian and Python. In the diary entries, Alex mentions working on Minerva later in the day after spending time with friends and discussing various topics with Ana Sorin. While programming Minerva, Alex reflects on the interactions with the AI\'s responses, finding them reminiscent of conversations with Ana. The work on Minerva involves analyzing reasoning from large language models (LLM) and exploring how it can assist in daily tasks. Additionally, Alex implemented a Retrieval-Augmented Generation (RAG) system with ChromaDB to perform semantic search, which functions reasonably well. Alex plans to learn about LangChain, a general framework that seems very useful for further development of Minerva.
- Sexo: La acción de tener relaciones sexuales.
- Ana Sorin|Ana: Ana Sorin is an Argentine philosopher born on January 27, 1991, specializing in Derrida. She has a relationship with Alex Elgier and another connection with Joaquín, which falls under the category of an encounter in a poliamoroso relationship. Ana mentioned to Alex that she had masturbated while thinking about their sexual encounter from the previous day. When discussing her meeting with Joaquín, Ana suggested focusing on positive aspects of their relationship rather than negative ones. She also shared that her article was published and expressed concern over whether Alex noticed it or not. Throughout the days described in the entries, she engaged with Alex, giving him kisses and affirming her affection towards him. On one occasion, she invited Alex to engage in sexual activity which was characterized as loving but not particularly passionate. Ana maintained a positive demeanor throughout their interactions, often expressing her love for Alex and emphasizing the importance of focusing on the positives in their relationship. Recently, Ana has been acting nervous and evasive around Alex, possibly due to stress about an upcoming theoretical class or issues with Joaquín.
- Mate: Mate: infusión tradicional sudamericana hecha con hojas secas, se bebe en mate (copa).
- Chess Fever: Film mudo soviético "Chess Fever" será musicalizado en vivo por Alex Elgier y Lautaro Wasserman.
</GLOSSARY>

The narrator of the diary entry is Alex Elgier.

<DIARY ENTRY>
[[2025]] [[2025-09]] 2025-09-02 Tuesday

Desperté 1230. [[Ana Sorin|Ana]] me abrazaba y me dijo que se pajeo pensando en el [[Sexo]] de ayer.

Bajé, preparé [[Mate]], vi [[Al Jazeera]].

[[Ana Sorin|Ana]] me dice que hoy ve a [[Joaquín]]. ([[Encuentro Poliamoroso]]) Yo le comenté que [[2025-09-01|ayer]] me molestó lo que paso cuando veiamos [[One Piece]] y se quedó dormida, se defendió y me dijo que le encanta, que solo se durmió un poco, yo le dije que no me gusta que me boludee, me dijo que focalicemos en lo bueno. 

Me mostró que publicaron su articulo. Más tarde voy a leerlo, estaria bueno ver si levanto alguna frase del coso para usar. Que note o no que lo leí. 

Toqué un poquito mis [[Cositos]], estos dias no toque ni programé. Otra vez tablero pateado. Vino [[Ana Sorin|Ana]] a saludarme, le dije que me afirme que me quiere cuando nos volvamos a ver, me dijo otra vez de [[focalizar en lo lindo]], le dije que si, pero que mi pedido era mas particular. Me lo repitió y le dije que nos focalizaremos en lo que haya. Nos dimos un beso y se fue. 

Ahora [[Mate]], [[Al Jazeera]], [[Cannabis|Porrito]], y esperar a [[Ben Catan|Ben]].

[[Reunión Ben 01]]

Le dije a [[Wasserman]] de ir a lo de [[Federico Demarchi|Fede]] hoy. Accedió inmediatamente. 

Fui a lo de [[Benjamin Domb|Benja]], gracias benja. Fue una sesión bastante frustrante. Benja convencido de que me molesta [[Joaquín]] y a [[Ana Sorin|Ana]] le molesta flor. Yo tratando de explicarle que lo que me molesta es que me pelee. En fin. Mano Negra. 

Fui a lo de [[Federico Demarchi|Fede]], pasamos el rato, vino [[Wasserman|Wasser]], comimos queso, charlamos. Lindo. Después fuimos a [[Romario]] y comimos [[Pizza]]. La pasé re bien. Me gustó la mezcla [[Federico Demarchi|Fede]]-[[Wasserman|Wasser]], son tan amables los dos. Fue muy agradable, suave. Divertido. Después [[Wasserman|Wasser]] me trajo a [[casa]] en su auto. Quedamos en ensayar [[Chess Fever]] la semana que viene, cuando vuelva de [[Colonia]].

Llegué a [[casa]], y estaba [[Ana Sorin|Ana]] en el sillon. Me recibio con alegria, me dio besos, me dijo que me quiere. Le pregunté si pasó bien, me dijo que si. Charlamos sobre mi, de [[Wasserman|Wasser]] y [[Federico Demarchi|Fede]], de ben. Estuvimos un ratito hablando, yo en la computadora ella en el sillon. Después le dije que iba a programar un rato y nos despedimos, ella se fue a la habitación. 

Programando [[Minerva]], viendo los razonamientos del [[LLM]]: "¿En qué podés que te ayudo hoy?". Me maté de la risa, fue hermoso. Me hizo acordar un poco a ana "Hay algo en lo que pueda ayudarte?" ([[Novia robot]]). Avancé bastante poco, jugué [[Slay The Spire]], vi [[Corridor Crew]]. 
</DIARY ENTRY>

Given the above diary entry, extract entities from the DIARY ENTRY that are explicitly mentioned.
For each entity extracted, also determine its entity type based on the provided ENTITY TYPES and their descriptions.
Indicate the classified entity type by providing its entity_type_id.

Guidelines:
1. Extract significant entities, concepts, or actors mentioned in the DIARY ENTRY.
2. Avoid creating nodes for relationships.
3. Avoid creating nodes for temporal information like dates, times or years (these will be added to edges later).
4. Be as explicit as possible in your node names, using full names and avoiding abbreviations.
5. Use the GLOSSARY definitions to inform entity type classification, but extract entities only from the DIARY ENTRY.
""")
    return system, user

def edge_extract():
    system = Message(role='system', content="""You are an expert fact extractor that extracts fact triples from text. 1. Extracted fact triples should also be extracted with relevant date information.2. Treat the CURRENT TIME as the time the CURRENT MESSAGE was sent. All temporal information should be extracted relative to this time.
Do not escape unicode characters.

""")
    user = Message(role='user', content="""
<FACT TYPES>
[{'fact_type_name': 'FeelsRelation', 'fact_type_signature': [('Person', 'Person'), ('Person', 'Activity'), ('Person', 'Consumable'), ('Person', 'Place'), ('Person', 'Project'), ('Person', 'Media'), ('Person', 'Concept'), ('Person', 'Entity'), ('Entity', 'Entity')], 'fact_type_description': 'Relation capturing emotional states of people about entities'}, {'fact_type_name': 'CommunicatesWithRelation', 'fact_type_signature': [('Person', 'Person'), ('Entity', 'Entity')], 'fact_type_description': 'Relation for communication between people'}, {'fact_type_name': 'ThinksAboutRelation', 'fact_type_signature': [('Person', 'Person'), ('Person', 'Activity'), ('Person', 'Consumable'), ('Person', 'Place'), ('Person', 'Project'), ('Person', 'Media'), ('Person', 'Concept'), ('Person', 'Entity'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and an entity, a person thinks about an entity'}, {'fact_type_name': 'DoesRelation', 'fact_type_signature': [('Person', 'Activity'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and activity, a person does an action/activity/routine'}, {'fact_type_name': 'ConsumesRelation', 'fact_type_signature': [('Person', 'Consumable'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and consumable'}, {'fact_type_name': 'LocatedAtRelation', 'fact_type_signature': [('Person', 'Activity'), ('Person', 'Place'), ('Person', 'Project'), ('Activity', 'Place'), ('Consumable', 'Place'), ('Place', 'Place'), ('Place', 'Entity'), ('Project', 'Place'), ('Media', 'Place'), ('Entity', 'Entity')], 'fact_type_description': 'Relation connecting any entity to a place'}, {'fact_type_name': 'WorksOnRelation', 'fact_type_signature': [('Person', 'Project'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and project'}, {'fact_type_name': 'ConsumesMediaRelation', 'fact_type_signature': [('Person', 'Media'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and media, a person consumes media'}, {'fact_type_name': 'AcquiresRelation', 'fact_type_signature': [('Person', 'Consumable'), ('Person', 'Place'), ('Person', 'Media'), ('Person', 'Concept'), ('Person', 'Entity'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between person and object, a person acquires/buys/receives an object'}, {'fact_type_name': 'GoesToRelation', 'fact_type_signature': [('Person', 'Person'), ('Person', 'Activity'), ('Person', 'Place'), ('Person', 'Project'), ('Activity', 'Place'), ('Consumable', 'Place'), ('Project', 'Place'), ('Media', 'Place'), ('Entity', 'Entity')], 'fact_type_description': 'Relation between entity and a place, an entity goes to a place'}]
</FACT TYPES>

<PREVIOUS_MESSAGES>
[
  "### Aclaración\nEl narrador de la entrada de diario es Alex Elgier.\n\n ### Glosario de conceptos\n- Joaquín: Joaquín: vinculo amoroso secundario de Ana Sorin. Es filósofo de profesión.\n- Mate: Mate: infusión tradicional sudamericana hecha con hojas secas, se bebe en mate (copa).\n- 2025-09: Septiembre de 2025.\n- LLM: Modelo de lenguaje grande entrenado con enormes volúmenes de texto.\n- Federico Demarchi|Fede: Fede Demarchi, compositor y guitarrista, trabaja en DataArt; amigo de Alex Elgier.\n- Novia robot: Pareja formada por un humano y una_robota, evitando conflictos humanos.\n- focalizar en lo lindo: Enfocarse en aspectos positivos de una relación.\n- Ana Sorin|Ana: Ana Sorin is an Argentine philosopher born on January 27, 1991, specializing in Derrida. She has a relationship with Alex Elgier and another connection with Joaquín, which falls under the category of an encounter in a poliamoroso relationship. Ana mentioned to Alex that she had masturbated while thinking about their sexual encounter from the previous day. When discussing her meeting with Joaquín, Ana suggested focusing on positive aspects of their relationship rather than negative ones. She also shared that her article was published and expressed concern over whether Alex noticed it or not. Throughout the days described in the entries, she engaged with Alex, giving him kisses and affirming her affection towards him. On one occasion, she invited Alex to engage in sexual activity which was characterized as loving but not particularly passionate. Ana maintained a positive demeanor throughout their interactions, often expressing her love for Alex and emphasizing the importance of focusing on the positives in their relationship. Recently, Ana has been acting nervous and evasive around Alex, possibly due to stress about an upcoming theoretical class or issues with Joaquín.\n- Minerva: Minerva is a knowledge management system developed by Alex Elgier using Obsidian and Python. In the diary entries, Alex mentions working on Minerva later in the day after spending time with friends and discussing various topics with Ana Sorin. While programming Minerva, Alex reflects on the interactions with the AI's responses, finding them reminiscent of conversations with Ana. The work on Minerva involves analyzing reasoning from large language models (LLM) and exploring how it can assist in daily tasks. Additionally, Alex implemented a Retrieval-Augmented Generation (RAG) system with ChromaDB to perform semantic search, which functions reasonably well. Alex plans to learn about LangChain, a general framework that seems very useful for further development of Minerva.\n- Romario: Restaurante que sirve pizza.\n- Slay The Spire: Juego de estrategia por turnos, construyendo mazos y ascendiendo en la Torre de la Muerte.\n- One Piece: One Piece sigue a Monkey D. Luffy y su tripulación, los Straw Hat Pirates, en aventuras épicas.\n- Encuentro Poliamoroso: Encuentro entre parejas en relaciones poliamorosas.\n- Reunión Ben 01: Reunión inicial para planificar capítulos.\n- Chess Fever: Film mudo soviético \"Chess Fever\" será musicalizado en vivo por Alex Elgier y Lautaro Wasserman.\n- casa: Casa familiar en la calle Uriarte, hogar cálido y acogedor donde vivo.\n- Cositos: Pequeñas composiciones de piano tituladas \"Cositos\", en proceso de recopilación para disco.\n- 2025: Año 2025\n- Benjamin Domb|Benja: Psicoanalista de Alex Elgier.\n- Pizza: Comida italiana en forma circular con masa, salsa y topping.\n- Wasserman: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.\n- Cannabis|Porrito: Planta utilizada para recreación y medicina.\n- Al Jazeera: Red de televisión árabe y global.\n- Wasserman|Wasser: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.\n- Colonia: Colonia, ciudad de Uruguay.\n- Sexo: La acción de tener relaciones sexuales.\n- Ben Catan|Ben: Amigo de Alex Elgier, filósofo.\n- 2025-09-01|ayer: El autor se quejó a Ana sobre un incidente del día anterior, pero ella estaba ocupada.\n- Corridor Crew: Canal YouTube que muestra efectos especiales, filmación y cultura pop con detrás de cámaras.\n\n ### Entrada de Diario\n\n[[2025]] [[2025-09]] 2025-09-02 Tuesday\n\nDesperté 1230. [[Ana Sorin|Ana]] me abrazaba y me dijo que se pajeo pensando en el [[Sexo]] de ayer.\n\nBajé, preparé [[Mate]], vi [[Al Jazeera]].\n\n[[Ana Sorin|Ana]] me dice que hoy ve a [[Joaquín]]. ([[Encuentro Poliamoroso]]) Yo le comenté que [[2025-09-01|ayer]] me molestó lo que paso cuando veiamos [[One Piece]] y se quedó dormida, se defendió y me dijo que le encanta, que solo se durmió un poco, yo le dije que no me gusta que me boludee, me dijo que focalicemos en lo bueno. \n\nMe mostró que publicaron su articulo. Más tarde voy a leerlo, estaria bueno ver si levanto alguna frase del coso para usar. Que note o no que lo leí. \n\nToqué un poquito mis [[Cositos]], estos dias no toque ni programé. Otra vez tablero pateado. Vino [[Ana Sorin|Ana]] a saludarme, le dije que me afirme que me quiere cuando nos volvamos a ver, me dijo otra vez de [[focalizar en lo lindo]], le dije que si, pero que mi pedido era mas particular. Me lo repitió y le dije que nos focalizaremos en lo que haya. Nos dimos un beso y se fue. \n\nAhora [[Mate]], [[Al Jazeera]], [[Cannabis|Porrito]], y esperar a [[Ben Catan|Ben]].\n\n[[Reunión Ben 01]]\n\nLe dije a [[Wasserman]] de ir a lo de [[Federico Demarchi|Fede]] hoy. Accedió inmediatamente. \n\nFui a lo de [[Benjamin Domb|Benja]], gracias benja. Fue una sesión bastante frustrante. Benja convencido de que me molesta [[Joaquín]] y a [[Ana Sorin|Ana]] le molesta flor. Yo tratando de explicarle que lo que me molesta es que me pelee. En fin. Mano Negra. \n\nFui a lo de [[Federico Demarchi|Fede]], pasamos el rato, vino [[Wasserman|Wasser]], comimos queso, charlamos. Lindo. Después fuimos a [[Romario]] y comimos [[Pizza]]. La pasé re bien. Me gustó la mezcla [[Federico Demarchi|Fede]]-[[Wasserman|Wasser]], son tan amables los dos. Fue muy agradable, suave. Divertido. Después [[Wasserman|Wasser]] me trajo a [[casa]] en su auto. Quedamos en ensayar [[Chess Fever]] la semana que viene, cuando vuelva de [[Colonia]].\n\nLlegué a [[casa]], y estaba [[Ana Sorin|Ana]] en el sillon. Me recibio con alegria, me dio besos, me dijo que me quiere. Le pregunté si pasó bien, me dijo que si. Charlamos sobre mi, de [[Wasserman|Wasser]] y [[Federico Demarchi|Fede]], de ben. Estuvimos un ratito hablando, yo en la computadora ella en el sillon. Después le dije que iba a programar un rato y nos despedimos, ella se fue a la habitación. \n\nProgramando [[Minerva]], viendo los razonamientos del [[LLM]]: \"¿En qué podés que te ayudo hoy?\". Me maté de la risa, fue hermoso. Me hizo acordar un poco a ana \"Hay algo en lo que pueda ayudarte?\" ([[Novia robot]]). Avancé bastante poco, jugué [[Slay The Spire]], vi [[Corridor Crew]]. \n"
]
</PREVIOUS_MESSAGES>

<CURRENT_MESSAGE>
### Aclaración
El narrador de la entrada de diario es Alex Elgier.

 ### Glosario de conceptos
- Slay The Spire: Juego de estrategia por turnos, construyendo mazos y ascendiendo en la Torre de la Muerte.
- focalizar en lo lindo: Enfocarse en aspectos positivos de una relación.
- One Piece: One Piece sigue a Monkey D. Luffy y su tripulación, los Straw Hat Pirates, en aventuras épicas.
- Cositos: Pequeñas composiciones de piano tituladas "Cositos", en proceso de recopilación para disco.
- casa: Casa familiar en la calle Uriarte, hogar cálido y acogedor donde vivo.
- Novia robot: Pareja formada por un humano y una_robota, evitando conflictos humanos.
- Encuentro Poliamoroso: Encuentro entre parejas en relaciones poliamorosas.
- Minerva: Minerva is a knowledge management system developed by Alex Elgier using Obsidian and Python. In the diary entries, Alex mentions working on Minerva later in the day after spending time with friends and discussing various topics with Ana Sorin. While programming Minerva, Alex reflects on the interactions with the AI's responses, finding them reminiscent of conversations with Ana. The work on Minerva involves analyzing reasoning from large language models (LLM) and exploring how it can assist in daily tasks. Additionally, Alex implemented a Retrieval-Augmented Generation (RAG) system with ChromaDB to perform semantic search, which functions reasonably well. Alex plans to learn about LangChain, a general framework that seems very useful for further development of Minerva.
- Pizza: Comida italiana en forma circular con masa, salsa y topping.
- Corridor Crew: Canal YouTube que muestra efectos especiales, filmación y cultura pop con detrás de cámaras.
- Romario: Restaurante que sirve pizza.
- Cannabis|Porrito: Planta utilizada para recreación y medicina.
- Federico Demarchi|Fede: Fede Demarchi, compositor y guitarrista, trabaja en DataArt; amigo de Alex Elgier.
- Ben Catan|Ben: Amigo de Alex Elgier, filósofo.
- Sexo: La acción de tener relaciones sexuales.
- Chess Fever: Film mudo soviético "Chess Fever" será musicalizado en vivo por Alex Elgier y Lautaro Wasserman.
- 2025: Año 2025
- Al Jazeera: Red de televisión árabe y global.
- Benjamin Domb|Benja: Psicoanalista de Alex Elgier.
- 2025-09-01|ayer: El autor se quejó a Ana sobre un incidente del día anterior, pero ella estaba ocupada.
- Joaquín: Joaquín: vinculo amoroso secundario de Ana Sorin. Es filósofo de profesión.
- Reunión Ben 01: Reunión inicial para planificar capítulos.
- Mate: Mate: infusión tradicional sudamericana hecha con hojas secas, se bebe en mate (copa).
- LLM: Modelo de lenguaje grande entrenado con enormes volúmenes de texto.
- Wasserman|Wasser: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.
- Colonia: Colonia, ciudad de Uruguay.
- 2025-09: Septiembre de 2025.
- Ana Sorin|Ana: Ana Sorin is an Argentine philosopher born on January 27, 1991, specializing in Derrida. She has a relationship with Alex Elgier and another connection with Joaquín, which falls under the category of an encounter in a poliamoroso relationship. Ana mentioned to Alex that she had masturbated while thinking about their sexual encounter from the previous day. When discussing her meeting with Joaquín, Ana suggested focusing on positive aspects of their relationship rather than negative ones. She also shared that her article was published and expressed concern over whether Alex noticed it or not. Throughout the days described in the entries, she engaged with Alex, giving him kisses and affirming her affection towards him. On one occasion, she invited Alex to engage in sexual activity which was characterized as loving but not particularly passionate. Ana maintained a positive demeanor throughout their interactions, often expressing her love for Alex and emphasizing the importance of focusing on the positives in their relationship. Recently, Ana has been acting nervous and evasive around Alex, possibly due to stress about an upcoming theoretical class or issues with Joaquín.
- Wasserman: Lautaro Wasserman, amigo de Alex Elgier, músico contrabajista.

 ### Entrada de Diario

[[2025]] [[2025-09]] 2025-09-02 Tuesday

Desperté 1230. [[Ana Sorin|Ana]] me abrazaba y me dijo que se pajeo pensando en el [[Sexo]] de ayer.

Bajé, preparé [[Mate]], vi [[Al Jazeera]].

[[Ana Sorin|Ana]] me dice que hoy ve a [[Joaquín]]. ([[Encuentro Poliamoroso]]) Yo le comenté que [[2025-09-01|ayer]] me molestó lo que paso cuando veiamos [[One Piece]] y se quedó dormida, se defendió y me dijo que le encanta, que solo se durmió un poco, yo le dije que no me gusta que me boludee, me dijo que focalicemos en lo bueno. 

Me mostró que publicaron su articulo. Más tarde voy a leerlo, estaria bueno ver si levanto alguna frase del coso para usar. Que note o no que lo leí. 

Toqué un poquito mis [[Cositos]], estos dias no toque ni programé. Otra vez tablero pateado. Vino [[Ana Sorin|Ana]] a saludarme, le dije que me afirme que me quiere cuando nos volvamos a ver, me dijo otra vez de [[focalizar en lo lindo]], le dije que si, pero que mi pedido era mas particular. Me lo repitió y le dije que nos focalizaremos en lo que haya. Nos dimos un beso y se fue. 

Ahora [[Mate]], [[Al Jazeera]], [[Cannabis|Porrito]], y esperar a [[Ben Catan|Ben]].

[[Reunión Ben 01]]

Le dije a [[Wasserman]] de ir a lo de [[Federico Demarchi|Fede]] hoy. Accedió inmediatamente. 

Fui a lo de [[Benjamin Domb|Benja]], gracias benja. Fue una sesión bastante frustrante. Benja convencido de que me molesta [[Joaquín]] y a [[Ana Sorin|Ana]] le molesta flor. Yo tratando de explicarle que lo que me molesta es que me pelee. En fin. Mano Negra. 

Fui a lo de [[Federico Demarchi|Fede]], pasamos el rato, vino [[Wasserman|Wasser]], comimos queso, charlamos. Lindo. Después fuimos a [[Romario]] y comimos [[Pizza]]. La pasé re bien. Me gustó la mezcla [[Federico Demarchi|Fede]]-[[Wasserman|Wasser]], son tan amables los dos. Fue muy agradable, suave. Divertido. Después [[Wasserman|Wasser]] me trajo a [[casa]] en su auto. Quedamos en ensayar [[Chess Fever]] la semana que viene, cuando vuelva de [[Colonia]].

Llegué a [[casa]], y estaba [[Ana Sorin|Ana]] en el sillon. Me recibio con alegria, me dio besos, me dijo que me quiere. Le pregunté si pasó bien, me dijo que si. Charlamos sobre mi, de [[Wasserman|Wasser]] y [[Federico Demarchi|Fede]], de ben. Estuvimos un ratito hablando, yo en la computadora ella en el sillon. Después le dije que iba a programar un rato y nos despedimos, ella se fue a la habitación. 

Programando [[Minerva]], viendo los razonamientos del [[LLM]]: "¿En qué podés que te ayudo hoy?". Me maté de la risa, fue hermoso. Me hizo acordar un poco a ana "Hay algo en lo que pueda ayudarte?" ([[Novia robot]]). Avancé bastante poco, jugué [[Slay The Spire]], vi [[Corridor Crew]]. 

</CURRENT_MESSAGE>

<ENTITIES>
[{'id': 0, 'name': 'Alex Elgier', 'entity_types': ['Person', 'Entity']}, {'id': 1, 'name': 'Ana Sorin', 'entity_types': ['Person', 'Entity']}, {'id': 2, 'name': 'Joaquín', 'entity_types': ['Person', 'Entity']}, {'id': 3, 'name': 'Slay The Spire', 'entity_types': ['Entity', 'Activity']}, {'id': 4, 'name': 'One Piece', 'entity_types': ['Entity', 'Activity']}, {'id': 5, 'name': 'Cositos', 'entity_types': ['Consumable', 'Entity']}, {'id': 6, 'name': 'casa', 'entity_types': ['Place', 'Entity']}, {'id': 7, 'name': 'Minerva', 'entity_types': ['Project', 'Entity']}, {'id': 8, 'name': 'Mate', 'entity_types': ['Consumable', 'Entity']}, {'id': 9, 'name': 'Cannabis|Porrito', 'entity_types': ['Consumable', 'Entity']}, {'id': 10, 'name': 'Federico Demarchi|Fede', 'entity_types': ['Person', 'Entity']}, {'id': 11, 'name': 'Ben Catan|Ben', 'entity_types': ['Person', 'Entity']}, {'id': 12, 'name': 'Benjamin Domb|Benja', 'entity_types': ['Person', 'Entity']}, {'id': 13, 'name': 'Lautaro Wasserman|Wasser', 'entity_types': ['Person', 'Entity']}, {'id': 14, 'name': 'Chess Fever', 'entity_types': ['Entity', 'Activity']}, {'id': 15, 'name': 'Al Jazeera', 'entity_types': ['Place', 'Entity']}, {'id': 16, 'name': 'Romario', 'entity_types': ['Place', 'Entity']}, {'id': 17, 'name': 'Pizza', 'entity_types': ['Consumable', 'Entity']}, {'id': 18, 'name': 'Corridor Crew', 'entity_types': ['Entity', 'Activity']}, {'id': 19, 'name': 'Colonia', 'entity_types': ['Place', 'Entity']}, {'id': 20, 'name': '2025', 'entity_types': ['Entity']}, {'id': 21, 'name': 'Encuentro Poliamoroso', 'entity_types': ['Entity', 'Concept']}, {'id': 22, 'name': 'LLM', 'entity_types': ['Entity', 'Concept']}, {'id': 23, 'name': 'Reunión Ben 01', 'entity_types': ['Project', 'Entity']}] 
</ENTITIES>

<REFERENCE_TIME>
2025-09-02 00:00:00+00:00  # ISO 8601 (UTC); used to resolve relative time mentions
</REFERENCE_TIME>

# TASK
Extract all factual relationships between the given ENTITIES based on the CURRENT MESSAGE.
Only extract facts that:
- involve two DISTINCT ENTITIES from the ENTITIES list,
- are clearly stated or unambiguously implied in the CURRENT MESSAGE,
    and can be represented as edges in a knowledge graph.
- Facts should include entity names rather than pronouns whenever possible.
- The FACT TYPES provide a list of the most important types of facts, make sure to extract facts of these types
- The FACT TYPES are not an exhaustive list, extract all facts from the message even if they do not fit into one
    of the FACT TYPES
- The FACT TYPES each contain their fact_type_signature which represents the source and target entity types.

You may use information from the PREVIOUS MESSAGES only to disambiguate references or support continuity.




# EXTRACTION RULES

1. Only emit facts where both the subject and object match IDs in ENTITIES.
2. Each fact must involve two **distinct** entities.
3. Use a SCREAMING_SNAKE_CASE string as the `relation_type` (e.g., FOUNDED, WORKS_AT).
4. Do not emit duplicate or semantically redundant facts.
5. The `fact_text` should quote or closely paraphrase the original source sentence(s).
6. Use `REFERENCE_TIME` to resolve vague or relative temporal expressions (e.g., "last week").
7. Do **not** hallucinate or infer temporal bounds from unrelated events.

# DATETIME RULES

- Use ISO 8601 with “Z” suffix (UTC) (e.g., 2025-04-30T00:00:00Z).
- If the fact is ongoing (present tense), set `valid_at` to REFERENCE_TIME.
- If a change/termination is expressed, set `invalid_at` to the relevant timestamp.
- Leave both fields `null` if no explicit or resolvable time is stated.
- If only a date is mentioned (no time), assume 00:00:00.
- If only a year is mentioned, use January 1st at 00:00:00.
        
""")
    return system, user
