import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

// vue-i18n / vue-router mock (마운트 의존성 단순화)
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (k) => k }) }))
const push = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }))

// api mock — createSimulation 성공, uploadProfiles 스파이
const { createSimulation, uploadProfiles } = vi.hoisted(() => ({
  createSimulation: vi.fn(() => Promise.resolve({ success: true, data: { simulation_id: 'sim_x' } })),
  uploadProfiles: vi.fn(() => Promise.resolve({ success: true, count: 3 })),
}))
vi.mock('../../api/simulation', () => ({ createSimulation, uploadProfiles }))

import Step1GraphBuild from '../Step1GraphBuild.vue'

function jsonFile(obj) {
  return new File([JSON.stringify(obj)], 'profiles.json', { type: 'application/json' })
}

// 마이크로태스크 + 매크로태스크(File.text/FileReader) 모두 배수
async function settle() {
  await flushPromises()
  await new Promise((r) => setTimeout(r, 20))
  await flushPromises()
}

const baseProps = {
  currentPhase: 2,
  projectData: { project_id: 'proj_1', graph_id: 'g1', ontology: { entity_types: [], edge_types: [] } },
  graphData: { node_count: 3 },
}

beforeEach(() => { createSimulation.mockClear(); uploadProfiles.mockClear(); push.mockClear() })

describe('Step1GraphBuild 프로필 주입 wiring (T-035 / FR-004, FR-008)', () => {
  it('프로필 주입 모드 → createSimulation 후 uploadProfiles 호출', async () => {
    const profs = [{ user_id: 0, user_name: 'u0', name: 'n', bio: 'b', persona: 'p' }]
    const w = mount(Step1GraphBuild, {
      props: { ...baseProps, injectionConfig: { profileMode: 'inject', profileFile: jsonFile(profs) } },
      global: { mocks: { $t: (k) => k } },
    })
    await w.find('button.action-btn').trigger('click')
    await settle()
    expect(createSimulation).toHaveBeenCalled()
    expect(uploadProfiles).toHaveBeenCalledWith({ simulation_id: 'sim_x', profiles: profs })
    expect(push).toHaveBeenCalled()
  })

  it('프로필 생성 모드 → uploadProfiles 미호출', async () => {
    const w = mount(Step1GraphBuild, {
      props: { ...baseProps, injectionConfig: { profileMode: 'generate', profileFile: null } },
      global: { mocks: { $t: (k) => k } },
    })
    await w.find('button.action-btn').trigger('click')
    await settle()
    expect(createSimulation).toHaveBeenCalled()
    expect(uploadProfiles).not.toHaveBeenCalled()
  })
})
