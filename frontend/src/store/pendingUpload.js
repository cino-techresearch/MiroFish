/**
 * 临时存储待上传的文件和需求 + 레이어 주입 설정(FR-008)
 * 用于首页点击启动引擎后立即跳转，在Process页面再进行API调用
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
