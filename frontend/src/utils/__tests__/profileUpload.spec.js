import { describe, it, expect, vi } from 'vitest'
import { readProfilesFromFile, submitInjectedProfiles } from '../profileUpload'

function jsonFile(obj, name = 'profiles.json') {
  return new File([JSON.stringify(obj)], name, { type: 'application/json' })
}

describe('readProfilesFromFile (T-029 / FR-004)', () => {
  it('JSON File → 프로필 배열 파싱', async () => {
    const profs = [{ user_id: 0, user_name: 'u0' }]
    const out = await readProfilesFromFile(jsonFile(profs))
    expect(out).toEqual(profs)
  })

  it('잘못된 JSON → 에러', async () => {
    const bad = new File(['not json'], 'x.json', { type: 'application/json' })
    await expect(readProfilesFromFile(bad)).rejects.toThrow()
  })
})

describe('submitInjectedProfiles (T-029 / FR-004, FR-008) — uploadProfiles 호출', () => {
  it('File 을 읽어 {simulation_id, profiles} 로 uploadProfiles 호출', async () => {
    const uploadProfiles = vi.fn(() => Promise.resolve({ success: true, count: 1 }))
    const profs = [{ user_id: 0, user_name: 'u0', name: 'n', bio: 'b', persona: 'p' }]
    const resp = await submitInjectedProfiles('sim_1', jsonFile(profs), { uploadProfiles })
    expect(uploadProfiles).toHaveBeenCalledWith({ simulation_id: 'sim_1', profiles: profs })
    expect(resp.count).toBe(1)
  })
})
