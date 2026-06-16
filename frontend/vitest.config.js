import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// 프론트엔드 컴포넌트/유닛 테스트용 vitest 설정 (NFR-003)
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts}'],
  },
})
