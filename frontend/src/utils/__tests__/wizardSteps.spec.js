import { describe, it, expect } from 'vitest'
import { getWizardPlan, nextStep, ALL_STEPS } from '../wizardSteps'

describe('wizardSteps (T-026 / FR-008, DOD-006, TS-011)', () => {
  it('생성/생성: 전체 스텝, 스킵 없음', () => {
    const plan = getWizardPlan({ skipOntologySteps: false, skipProfileGeneration: false })
    expect(plan.steps).toEqual(ALL_STEPS)
    expect(plan.skippedSteps).toEqual([])
    expect(plan.useInjectedProfiles).toBe(false)
  })

  it('온톨로지 주입: graphBuild 스텝 스킵', () => {
    const plan = getWizardPlan({ skipOntologySteps: true })
    expect(plan.steps).not.toContain('graphBuild')
    expect(plan.skippedSteps).toContain('graphBuild')
  })

  it('프로필 주입: useInjectedProfiles=true (prepare 는 유지)', () => {
    const plan = getWizardPlan({ skipProfileGeneration: true })
    expect(plan.useInjectedProfiles).toBe(true)
    expect(plan.steps).toContain('prepare')
  })

  it('둘 다 주입: graphBuild 스킵 + useInjectedProfiles', () => {
    const plan = getWizardPlan({ skipOntologySteps: true, skipProfileGeneration: true })
    expect(plan.steps).not.toContain('graphBuild')
    expect(plan.useInjectedProfiles).toBe(true)
  })

  it('nextStep: 온톨로지 주입 시 graphBuild 건너뛰고 prepare 로 시작', () => {
    // 스킵된 첫 활성 스텝은 prepare
    const plan = getWizardPlan({ skipOntologySteps: true })
    expect(plan.steps[0]).toBe('prepare')
    expect(nextStep('prepare', { skipOntologySteps: true })).toBe('simulate')
  })
})
