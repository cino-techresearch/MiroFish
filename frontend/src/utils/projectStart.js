// 프로젝트 시작 시 주입/생성 결정 + 실제 주입 호출 (FR-008).
// Process.vue 가 이 헬퍼를 사용해 온톨로지 레이어를 주입(injectGraph)하거나 생성한다.
// api 를 인자로 받아 단위 테스트 가능하게 한다.

/**
 * 온톨로지 레이어 동작 결정.
 * @returns {'inject'|'generate'}
 */
export function resolveOntologyAction(injectionConfig = {}) {
  return injectionConfig.ontologyMode === 'inject' ? 'inject' : 'generate'
}

/**
 * 기존 graph_id 주입을 실제 호출한다.
 * @param {Object} injectionConfig - { graphId }
 * @param {string} simulationRequirement
 * @param {{injectGraph: Function}} api
 * @returns {Promise<Object>} injectGraph 응답
 */
export async function startInjection(injectionConfig, simulationRequirement, api) {
  return api.injectGraph({
    graph_id: injectionConfig.graphId,
    simulation_requirement: simulationRequirement,
  })
}
