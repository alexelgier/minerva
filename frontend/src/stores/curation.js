import { defineStore } from 'pinia'
import { ref } from 'vue'


export const useCurationStore = defineStore('curation', () => {
  const entities = ref([])
  const currentEntityIndex = ref(0)
  const editedEntity = ref({})
  const journalMarkdown = ref("")

    // State
    const journalGroups = ref([])
    const stats = ref({})
    const isLoading = ref(false)
    const error = ref(null)

    // Actions
    async function fetchCurationQueue() {
      isLoading.value = true
      error.value = null
      try {
        const response = await fetch('http://127.0.0.1:8000/api/curation/pending')
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
        const data = await response.json()
        // Pre-process tasks for easier display
        (data.journal_entry || []).forEach(journal => {
          (journal.tasks || []).forEach(task => {
            if (task.type === 'entity') {
              task.displayName = task.data.name
              task.displayType = task.data.entity_type || task.data.type || 'Entity'
            } else if (task.type === 'relationship') {
              task.displayName = task.data.proposed_types ? task.data.proposed_types.join(', ') : task.data.relationship_type
              task.displayType = 'Relationship'
            } else {
              task.displayName = task.data.name || task.id
              task.displayType = task.type || 'Unknown'
            }
          })
        })
        journalGroups.value = data.journal_entry || []
        stats.value = data.stats || {}
      } catch (err) {
        error.value = `Failed to load data: ${err.message}. Make sure the API server is running on port 8000.`
      } finally {
        isLoading.value = false
      }
    }

    async function handleCurationAction(group, taskIndex, action) {
      const task = group.tasks[taskIndex]
      try {
        const payload = {
          action: action,
          curated_data: action === 'accept' ? task.data : {},
        }
        const task_type = task.type === 'entity' ? 'entities' : 'relationships'
        const response = await fetch(`http://127.0.0.1:8000/api/curation/${task_type}/${task.journal_id}/${task.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
        }
        group.tasks.splice(taskIndex, 1)
      } catch (err) {
        error.value = `Failed to ${action} '${task.displayName}': ${err.message}.`
      }
    }

    async function submitCuration(group) {
      try {
        isLoading.value = true
        error.value = null
        const response = await fetch(`http://127.0.0.1:8000/api/curation/${group.phase}/${group.journal_id}/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
        await response.json() // Remove unused variable assignment
        // Remove the completed journal from the list
        const groupIndex = journalGroups.value.findIndex(j => j.journal_id === group.journal_id)
        if (groupIndex > -1) journalGroups.value.splice(groupIndex, 1)
      } catch (err) {
        error.value = `Failed to complete curation: ${err.message}.`
      } finally {
        isLoading.value = false
      }
    }

    // Existing entity editing logic
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
      journalGroups,
      stats,
      isLoading,
      error,
      fetchCurationQueue,
      handleCurationAction,
      submitCuration,
      setEntities,
      setCurrentEntityIndex,
      setEditedEntity,
      updateField,
      resetEdits,
      initializeMockEntities,
    }
  })
