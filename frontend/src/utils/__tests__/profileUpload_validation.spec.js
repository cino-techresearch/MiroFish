import { describe, it, expect } from 'vitest'
import { readProfilesFromFile } from '../profileUpload'

function file(content) {
  return new File([content], 'p.json', { type: 'application/json' })
}

describe('readProfilesFromFile shape 검증 (T-039 / FR-004)', () => {
  it('비어 있지 않은 배열 → 통과', async () => {
    const out = await readProfilesFromFile(file(JSON.stringify([{ user_id: 0 }])))
    expect(out).toEqual([{ user_id: 0 }])
  })

  it('배열이 아니면 거부', async () => {
    await expect(readProfilesFromFile(file('{"user_id":0}'))).rejects.toThrow(/배열/)
  })

  it('빈 배열이면 거부', async () => {
    await expect(readProfilesFromFile(file('[]'))).rejects.toThrow(/비어/)
  })

  it('잘못된 JSON 이면 거부', async () => {
    await expect(readProfilesFromFile(file('nope'))).rejects.toThrow(/JSON/)
  })
})
