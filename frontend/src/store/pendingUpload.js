/**
 * Temporarily stores files and requirements pending upload + layer injection settings (FR-008)
 * Used to navigate immediately after clicking "Start Engine" on the home page,
 * then perform the API call on the Process page
 */
import { reactive } from 'vue'

const DEFAULT_INJECTION = { ontologyMode: 'generate', profileMode: 'generate', graphId: '', profileFile: null }

const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false,
  injection: { ...DEFAULT_INJECTION }
})

export function setPendingUpload(files, requirement, injection = {}) {
  state.files = files
  state.simulationRequirement = requirement
  state.injection = { ...DEFAULT_INJECTION, ...injection }
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    isPending: state.isPending,
    injection: state.injection
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.injection = { ...DEFAULT_INJECTION }
  state.isPending = false
}

export default state
