// 마법사 스텝 시퀀싱 — 주입 레이어에 따라 스텝을 스킵한다 (FR-008, DOD-006).
// Process.vue 가 이 순수 함수를 사용해 표시할 스텝과 prepare 모드를 결정한다.

export const ALL_STEPS = ['graphBuild', 'prepare', 'simulate', 'report', 'interact']

/**
 * 주입 설정에 따른 마법사 계획을 계산한다.
 * @param {Object} config - InjectionPanel 의 change 이벤트 payload
 *   { skipOntologySteps?: boolean, skipProfileGeneration?: boolean }
 * @returns {{ steps: string[], useInjectedProfiles: boolean, skippedSteps: string[] }}
 */
export function getWizardPlan(config = {}) {
  const skipOntology = !!config.skipOntologySteps
  const useInjectedProfiles = !!config.skipProfileGeneration

  const skippedSteps = []
  // 온톨로지 주입(기존 graph_id 재사용) 시 그래프 구축 스텝을 건너뛴다.
  if (skipOntology) skippedSteps.push('graphBuild')

  const steps = ALL_STEPS.filter((s) => !skippedSteps.includes(s))

  return { steps, useInjectedProfiles, skippedSteps }
}

/**
 * 현재 스텝 다음의 활성 스텝을 반환한다 (스킵된 스텝은 건너뜀).
 * @returns {string|null} 다음 스텝 id 또는 마지막이면 null
 */
export function nextStep(current, config = {}) {
  const { steps } = getWizardPlan(config)
  const idx = steps.indexOf(current)
  if (idx === -1 || idx === steps.length - 1) return null
  return steps[idx + 1]
}
