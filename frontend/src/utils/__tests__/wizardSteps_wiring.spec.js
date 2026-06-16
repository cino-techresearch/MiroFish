import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

// MainView 가 getWizardPlan 을 production 에서 실제 사용하는지(dead util 아님) 검증 (T-038 / FR-008)
const mainViewSrc = readFileSync(
  fileURLToPath(new URL('../../views/MainView.vue', import.meta.url)),
  'utf-8'
)

describe('wizardSteps production 배선 (T-038)', () => {
  it('MainView 가 getWizardPlan 을 import 한다', () => {
    expect(mainViewSrc).toContain("from '../utils/wizardSteps'")
    expect(mainViewSrc).toContain('getWizardPlan')
  })

  it('MainView 가 skippedSteps 로 스텝 전이를 구동한다', () => {
    expect(mainViewSrc).toContain('skippedSteps')
    expect(mainViewSrc).toMatch(/getWizardPlan\(injectionConfig\.value\)/)
  })
})
