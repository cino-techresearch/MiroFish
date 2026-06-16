import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import InjectionPanel from '../InjectionPanel.vue'
import { getWizardPlan, ALL_STEPS } from '../../utils/wizardSteps'

// InjectionPanel 의 선택 → change payload → 마법사 스텝 스킵까지 end-to-end 검증
// (T-027 / DOD-006, TS-011)
async function selectCombo(ontology, profile) {
  const w = mount(InjectionPanel)
  await w.find('[data-testid="ontology-mode"]').setValue(ontology)
  await w.find('[data-testid="profile-mode"]').setValue(profile)
  const payload = w.emitted('change').at(-1)[0]
  return { w, payload, plan: getWizardPlan(payload) }
}

describe('주입 4조합 → 스텝 스킵 통합 (T-027)', () => {
  it('생성+생성: 전체 스텝, 주입 입력 없음', async () => {
    const { w, plan } = await selectCombo('generate', 'generate')
    expect(plan.steps).toEqual(ALL_STEPS)
    expect(w.find('[data-testid="graph-id-input"]').exists()).toBe(false)
    expect(w.find('[data-testid="profile-file-input"]').exists()).toBe(false)
  })

  it('온톨로지 주입+프로필 생성: graphBuild 스킵, graph_id 입력 노출', async () => {
    const { w, plan } = await selectCombo('inject', 'generate')
    expect(plan.steps).not.toContain('graphBuild')
    expect(plan.useInjectedProfiles).toBe(false)
    expect(w.find('[data-testid="graph-id-input"]').exists()).toBe(true)
  })

  it('온톨로지 생성+프로필 주입: 전체 스텝 유지, useInjectedProfiles, 파일 입력 노출', async () => {
    const { w, plan } = await selectCombo('generate', 'inject')
    expect(plan.steps).toContain('graphBuild')
    expect(plan.useInjectedProfiles).toBe(true)
    expect(w.find('[data-testid="profile-file-input"]').exists()).toBe(true)
  })

  it('온톨로지 주입+프로필 주입: graphBuild 스킵 + useInjectedProfiles + 두 입력 노출', async () => {
    const { w, plan } = await selectCombo('inject', 'inject')
    expect(plan.steps).not.toContain('graphBuild')
    expect(plan.useInjectedProfiles).toBe(true)
    expect(w.find('[data-testid="graph-id-input"]').exists()).toBe(true)
    expect(w.find('[data-testid="profile-file-input"]').exists()).toBe(true)
  })
})
