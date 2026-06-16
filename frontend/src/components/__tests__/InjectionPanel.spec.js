import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import InjectionPanel from '../InjectionPanel.vue'

describe('InjectionPanel (T-025 / FR-008, TS-011)', () => {
  it('기본은 생성/생성 — 주입 입력 미표시', () => {
    const w = mount(InjectionPanel)
    expect(w.find('[data-testid="graph-id-input"]').exists()).toBe(false)
    expect(w.find('[data-testid="profile-file-input"]').exists()).toBe(false)
  })

  it('온톨로지 주입 선택 시 graph_id 입력 노출 + skip 신호 emit', async () => {
    const w = mount(InjectionPanel)
    await w.find('[data-testid="ontology-mode"]').setValue('inject')
    expect(w.find('[data-testid="graph-id-input"]').exists()).toBe(true)
    const ev = w.emitted('change').at(-1)[0]
    expect(ev.ontologyMode).toBe('inject')
    expect(ev.skipOntologySteps).toBe(true)
  })

  it('프로필 주입 선택 시 파일 입력 노출 + skip 신호 emit', async () => {
    const w = mount(InjectionPanel)
    await w.find('[data-testid="profile-mode"]').setValue('inject')
    expect(w.find('[data-testid="profile-file-input"]').exists()).toBe(true)
    const ev = w.emitted('change').at(-1)[0]
    expect(ev.profileMode).toBe('inject')
    expect(ev.skipProfileGeneration).toBe(true)
  })

  it('4조합 모두 선택 가능', async () => {
    const combos = [
      ['generate', 'generate'], ['inject', 'generate'],
      ['generate', 'inject'], ['inject', 'inject'],
    ]
    for (const [o, p] of combos) {
      const w = mount(InjectionPanel)
      await w.find('[data-testid="ontology-mode"]').setValue(o)
      await w.find('[data-testid="profile-mode"]').setValue(p)
      const ev = w.emitted('change').at(-1)[0]
      expect(ev.ontologyMode).toBe(o)
      expect(ev.profileMode).toBe(p)
    }
  })
})
