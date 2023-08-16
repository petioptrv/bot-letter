<template>
  <div>
    <v-btn :color="color" @click="trigger"><slot>Choose File</slot></v-btn>
    <input :multiple="multiple" class="visually-hidden" type="file" v-on:change="files" ref="fileInput">
  </div>
</template>

<script lang="ts">
import { Component, Prop, Emit } from 'vue-property-decorator';
import {AdaptedVue} from "@/adaptedVue";

@Component
export default class UploadButton extends AdaptedVue {
  @Prop(String) public color: string | undefined;
  @Prop({default: false}) public multiple!: boolean;
  @Emit()
  public files(e): FileList {
    return e.target.files;
  }

  public trigger() {
    (this.$refs.fileInput as HTMLElement).click();
  }
}
</script>

<style scoped>
.visually-hidden {
  position: absolute !important;
  height: 1px;
  width: 1px;
  overflow: hidden;
  clip: rect(1px, 1px, 1px, 1px);
}
</style>
