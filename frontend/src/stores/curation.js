import { defineStore } from 'pinia'
import { ref } from 'vue'


export const useCurationStore = defineStore('curation', () => {
  const entities = ref([])
  const currentEntityIndex = ref(0)
  const editedEntity = ref({})
  const journalMarkdown = ref("")

  function setEntities(newEntities) {
    entities.value = newEntities
  }
  function setCurrentEntityIndex(idx) {
    currentEntityIndex.value = idx
  }
  function setEditedEntity(entity) {
    editedEntity.value = { ...entity }
  }
  function updateField(field, value) {
    editedEntity.value = { ...editedEntity.value, [field]: value }
  }
  function resetEdits() {
    editedEntity.value = { ...entities.value[currentEntityIndex.value] }
  }

  function initializeMockEntities() {
    // Example mock data, can be replaced with real API call
    setEntities([
      {
        type: 'Person',
        name: 'Ana Sorin',
        summary_short: 'Amiga, compañera',
        summary: 'Ana es una persona muy importante en mi vida.',
        uuid: 'person-ana',
        occupation: 'Filósofa',
        birth_date: '1990-01-01',
        spans: [
          { start: 45, end: 48 },
          { start: 120, end: 170 },
        ]
      },
      {
        type: 'Feeling',
        name: 'Cansancio',
        summary_short: 'Me sentí cansado al despertar',
        summary: 'Desperté cansado, con poca energía.',
        uuid: 'feeling-1',
        timestamp: '2025-09-09T13:00:00',
        intensity: 6,
        duration: 30,
        spans: {
          0: { start: 13, end: 21, label: 'Desperté' }
        }
      }
    ])
    setCurrentEntityIndex(0)
    setEditedEntity({ ...entities.value[0] })
    journalMarkdown.value = `[[2025]] [[2025-09]] [[2025-09-09]]  Tuesday

13:00 Desperté, cansado. [[Ana Sorin|Ana]] me ayudó a despertarme suavemente.

Bajé y me hice [[Mate]]. Tomé [[Mate]] y vi [[Al Jazeera]]. Hoy [[Israel]] bombardeó [[Qatar]], intentando matar líderes de [[Hamas]].

Seguí programando [[Minerva]]. Cambié el cliente, y lo hice streaming, para poder que pasa durante las inferencias largas. Está funcionando bien. Le tuve que sacar el caché. La forma en la que [[Graphiti]] construye los mensajes no me deja cachear correctamente. Cada vez más pienso que debería forkear el repo y hacer mi propia versión. 

[[Estudio de Piano|Práctica de Piano]]: Estudié [[Escala]], que hace varios días que no tocaba. También toqué mis [[Cositos]]. Buena práctica, corta pero está bien retomar. 

15:00 fui a la [[Terraza]] a saludar a [[Ana Sorin|Ana]], hay un solcito lindo y está cálido. [[Ana Sorin|Ana]] está enferma, parece estar empezando un resfrío, se la ve pálida. Me fumé un cigarrillo con ella, y volví para abajo a seguir trabajando en [[Minerva]].

15:45 viene [[Ben Catan|Ben]] a tener [[Reunión Ben 02]], vamos a seguir leyendo [[A Scanner Darkly]] para nuestro [[Proyectos]] [[Scanner]].

16:00 comí un [[Sandwich de Miga]]. 
[[Mate]], [[Al Jazeera]] y [[Minerva]] hasta que llegue [[Ben Catan|Ben]].

[[Reunión Ben 02]], muy buena reunión, fue una bocanada de aire fresca. Avanzamos leyendo capitulo 3 y 4. Me gusta como entiende las cosas [[Ben Catan|Ben]], es muy despierto y rápido, y compartimos puntos de vista. 

19:00, caminar hasta lo de [[Benjamin Domb|Benja]]. 
19:30, Sesión con [[Benjamin Domb|Benja]] muy buena, me sacó un peso de encima. "Si las heridas sanan pueden haber planes a largo plazo", la frase de cierre me dejó impactado. 

Cena con [[Federico Demarchi|Fede]], agradable. Comimos [[Lo de Rita]], [[Pechuga de Pollo]] con [[Puré Mixto]], y vimos unos videos de [[YouTube]] de la campeona de [[Ciclismo]].  

Cuando volví a [[casa]], [[Ana Sorin|Ana]] estaba arriba en la cama durmiendo con la compu y sus libros todos desplegados. Empece a despejar la cama y se despertó nerviosa, y se puso a trabajar de nuevo. Está muy resfriada, fui a hacerle un [[Té]]. Me vio de un humor sensiblemente mejorado, y me dijo 
- "Estás mas liviano"
- "Si" le respondí
- "Benja o Fede?"
- Me reí y le conteste "Ana, Benja, Fede. En ése orden." y después agregué "Y Ben! Tuve un buen dia."
    `
  }

  return {
    entities,
    currentEntityIndex,
    editedEntity,
    journalMarkdown,
    setEntities,
    setCurrentEntityIndex,
    setEditedEntity,
    updateField,
    resetEdits,
    initializeMockEntities,
  }
})
