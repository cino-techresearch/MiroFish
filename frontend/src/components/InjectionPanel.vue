<template>
  <div class="injection-panel">
    <div class="layer">
      <label>온톨로지 레이어</label>
      <select data-testid="ontology-mode" v-model="ontologyMode" @change="emitChange">
        <option value="generate">생성 (문서→온톨로지)</option>
        <option value="inject">주입 (기존 graph_id 재사용)</option>
      </select>
      <input
        v-if="ontologyMode === 'inject'"
        data-testid="graph-id-input"
        v-model="graphId"
        placeholder="기존 ZEP graph_id"
        @input="emitChange"
      />
    </div>

    <div class="layer">
      <label>페르소나 레이어</label>
      <select data-testid="profile-mode" v-model="profileMode" @change="emitChange">
        <option value="generate">생성 (ZEP 엔티티 기반)</option>
        <option value="inject">주입 (중립 JSON 프로필)</option>
      </select>
      <input
        v-if="profileMode === 'inject'"
        type="file"
        data-testid="profile-file-input"
        accept="application/json,.json"
        @change="onFile"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'InjectionPanel',
  emits: ['change'],
  data() {
    return {
      ontologyMode: 'generate',
      profileMode: 'generate',
      graphId: '',
      profileFile: null,
    }
  },
  methods: {
    onFile(e) {
      this.profileFile = e.target.files && e.target.files[0] ? e.target.files[0] : null
      this.emitChange()
    },
    emitChange() {
      this.$emit('change', {
        ontologyMode: this.ontologyMode,
        profileMode: this.profileMode,
        graphId: this.graphId,
        profileFile: this.profileFile,
        // 주입되는 레이어는 마법사에서 해당 스텝을 스킵한다 (FR-008)
        skipOntologySteps: this.ontologyMode === 'inject',
        skipProfileGeneration: this.profileMode === 'inject',
      })
    },
  },
}
</script>
