import { describe, it, expect, beforeEach } from 'vitest'
import { setPendingUpload, getPendingUpload, clearPendingUpload } from '../pendingUpload'

beforeEach(() => clearPendingUpload())

describe('pendingUpload 주입 설정 운반 (T-034 / FR-008)', () => {
  it('기본 주입 설정은 generate/generate', () => {
    setPendingUpload([], '요구')
    const p = getPendingUpload()
    expect(p.injection.ontologyMode).toBe('generate')
    expect(p.injection.profileMode).toBe('generate')
  })

  it('주입 설정을 저장/조회한다', () => {
    setPendingUpload([], '요구', { ontologyMode: 'inject', graphId: 'g1', profileMode: 'inject' })
    const p = getPendingUpload()
    expect(p.injection.ontologyMode).toBe('inject')
    expect(p.injection.graphId).toBe('g1')
    expect(p.injection.profileMode).toBe('inject')
  })

  it('clear 시 주입 설정도 초기화', () => {
    setPendingUpload([], 'x', { ontologyMode: 'inject', graphId: 'g' })
    clearPendingUpload()
    expect(getPendingUpload().injection.ontologyMode).toBe('generate')
    expect(getPendingUpload().isPending).toBe(false)
  })
})
