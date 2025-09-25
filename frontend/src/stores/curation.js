import { defineStore } from 'pinia'
import { ref } from 'vue'


export const useCurationStore = defineStore('curation', () => {
    // State
    const editedEntity = ref({})
    const journalEntries = ref({})
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
            journalEntries.value = data.journal_entries || {};
            stats.value = data.stats || {}
        } catch (err) {
            error.value = `Failed to load data: ${err.message}. Make sure the API server is running on port 8000.`
        } finally {
            isLoading.value = false
        }
    }

    async function handleCurationAction(group, taskuuid, action) {
        const task = group.tasks[taskuuid]
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
            delete group.tasks[taskuuid]
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
            if (group.journal_id && journalEntries.value[group.journal_id]) {
                delete journalEntries.value[group.journal_id]
            }
        } catch (err) {
            error.value = `Failed to complete curation: ${err.message}.`
        } finally {
            isLoading.value = false
        }
    }

    return {
        editedEntity,
        journalEntries,
        stats,
        isLoading,
        error,
        fetchCurationQueue,
        handleCurationAction,
        submitCuration,
    }
})
