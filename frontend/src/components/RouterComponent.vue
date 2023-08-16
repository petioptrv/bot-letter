<template>
  <router-view></router-view>
</template>

<script lang="ts">
import { Component } from 'vue-property-decorator';
import {AdaptedVue} from "@/adaptedVue";

@Component
export default class RouterComponent extends AdaptedVue {
}
</script>
