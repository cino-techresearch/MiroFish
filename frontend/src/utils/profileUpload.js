// 중립 JSON 프로필 File → uploadProfiles 글루 (FR-004, FR-008).
// InjectionPanel 이 emit 하는 profileFile(File) 을 읽어 백엔드 업로드 API 로 전송한다.

/**
 * JSON File 을 읽어 프로필 배열로 파싱한다.
 * @param {File} file
 * @returns {Promise<Array>}
 */
export function readProfilesFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        resolve(JSON.parse(reader.result))
      } catch (e) {
        reject(new Error('프로필 파일이 유효한 JSON 이 아닙니다: ' + e.message))
      }
    }
    reader.onerror = () => reject(reader.error || new Error('파일 읽기 실패'))
    reader.readAsText(file)
  })
}

/**
 * profileFile 을 읽어 {simulation_id, profiles} 로 uploadProfiles 를 호출한다.
 * @param {string} simulationId
 * @param {File} file
 * @param {{uploadProfiles: Function}} api
 * @returns {Promise<Object>} uploadProfiles 응답
 */
export async function submitInjectedProfiles(simulationId, file, api) {
  const profiles = await readProfilesFromFile(file)
  return api.uploadProfiles({ simulation_id: simulationId, profiles })
}
