import { describe, it, expect } from 'vitest'

// vitest 인프라 sanity (T-023 / TS-011 지원)
describe('vitest infra', () => {
  it('runs', () => {
    expect(1 + 1).toBe(2)
  })
})
