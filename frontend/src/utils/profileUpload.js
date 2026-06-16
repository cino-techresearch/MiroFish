// 중립 JSON 프로필 File → uploadProfiles 글루 (FR-004, FR-008).
// InjectionPanel 이 emit 하는 profileFile(File) 을 읽어 백엔드 업로드 API 로 전송한다.

/**
 * JSON File 을 읽어 프로필 배열로 파싱한다.
 * @param {File} file
 * @returns {Promise<Array>}
 */
export async function readProfilesFromFile(file) {
  // Blob.text() 은 promise 기반이라 await 체인이 정상 전파된다(FileReader 매크로태스크 회피).
  let text
  if (typeof file.text === 'function') {
    text = await file.text()
  } else {
    text = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => reject(reader.error || new Error('파일 읽기 실패'))
      reader.readAsText(file)
    })
  }
  let parsed
  try {
    parsed = JSON.parse(text)
  } catch (e) {
    throw new Error('프로필 파일이 유효한 JSON 이 아닙니다: ' + e.message)
  }
  // shape 검증: 비어 있지 않은 배열이어야 한다 (FR-004 fail-fast)
  if (!Array.isArray(parsed)) {
    throw new Error('프로필 파일은 JSON 배열이어야 합니다')
  }
  if (parsed.length === 0) {
    throw new Error('프로필 파일이 비어 있습니다 (최소 1개 프로필 필요)')
  }
  return parsed
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
