import { describe, it, expect, vi, beforeEach } from 'vitest'

// service 모듈 mock (axios 인스턴스). requestWithRetry 는 thunk 를 그대로 호출.
// vi.mock 은 호이스팅되므로 factory 가 참조할 값은 vi.hoisted 로 끌어올린다.
const { post } = vi.hoisted(() => ({ post: vi.fn(() => Promise.resolve({ success: true })) }))
vi.mock('../index', () => ({
  default: { post, get: vi.fn() },
  requestWithRetry: (fn) => fn(),
}))

import { injectGraph } from '../graph'
import { uploadProfiles } from '../simulation'

beforeEach(() => post.mockClear())

describe('injectGraph (T-024 / FR-008)', () => {
  it('POST /api/graph/inject/graph 로 graph_id+requirement 전송', async () => {
    await injectGraph({ graph_id: 'g1', simulation_requirement: 'req' })
    expect(post).toHaveBeenCalledWith('/api/graph/inject/graph', {
      graph_id: 'g1', simulation_requirement: 'req',
    })
  })
})

describe('uploadProfiles (T-024 / FR-008)', () => {
  it('POST /api/simulation/profiles/upload 로 simulation_id+profiles 전송', async () => {
    const profiles = [{ user_id: 0 }]
    await uploadProfiles({ simulation_id: 'sim1', profiles })
    expect(post).toHaveBeenCalledWith('/api/simulation/profiles/upload', {
      simulation_id: 'sim1', profiles,
    })
  })
})
