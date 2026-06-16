import { describe, it, expect, vi } from 'vitest'
import { resolveOntologyAction, startInjection } from '../projectStart'

describe('resolveOntologyAction (T-028 / FR-008)', () => {
  it('온톨로지 생성 모드 → generate', () => {
    expect(resolveOntologyAction({ ontologyMode: 'generate' })).toBe('generate')
  })
  it('온톨로지 주입 모드 → inject', () => {
    expect(resolveOntologyAction({ ontologyMode: 'inject' })).toBe('inject')
  })
  it('빈 설정 → generate(안전 기본값)', () => {
    expect(resolveOntologyAction({})).toBe('generate')
  })
})

describe('startInjection (T-028 / FR-008) — 실제 injectGraph 호출', () => {
  it('graphId+requirement 로 injectGraph 를 호출하고 응답 반환', async () => {
    const injectGraph = vi.fn(() => Promise.resolve({ success: true, project_id: 'proj_1' }))
    const resp = await startInjection(
      { graphId: 'g1' }, '예측 요구', { injectGraph },
    )
    expect(injectGraph).toHaveBeenCalledWith({ graph_id: 'g1', simulation_requirement: '예측 요구' })
    expect(resp.project_id).toBe('proj_1')
  })
})
