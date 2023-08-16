<template>
  <v-container fluid>
    <v-card class="ma-3 pa-3">
      <v-card-title primary-title>
        <div class="headline primary--text">User Profile</div>
      </v-card-title>
      <v-card-text>
        <div class="my-4">
          <div class="subheading secondary--text text--lighten-3">Full Name</div>
          <div class="title primary--text text--darken-2" v-if="userProfile && userProfile.full_name">{{userProfile.full_name}}</div>
          <div class="title primary--text text--darken-2" v-else>-----</div>
        </div>
        <div class="my-3">
          <div class="subheading secondary--text text--lighten-3">Email</div>
          <div class="title primary--text text--darken-2" v-if="userProfile && userProfile.email">{{userProfile.email}}</div>
          <div class="title primary--text text--darken-2" v-else>-----</div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn to="/main/profile/edit">Edit</v-btn>
        <v-btn to="/main/profile/password">Change password</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script lang="ts">
import { Component } from 'vue-property-decorator';
import { readUserProfile } from '@/store/main/getters';
import {AdaptedVue} from "@/adaptedVue";

@Component
export default class UserProfile extends AdaptedVue {
  get userProfile() {
    return readUserProfile(this.$store);
  }

  public goToEdit() {
    if (this.$route.path != '/main/profile/edit') {
      this.$router.adaptedPush('/main/profile/edit');
    }
  }

  public goToPassword() {
    if (this.$route.path != '/main/profile/password') {
      this.$router.adaptedPush('/main/profile/password');
    }
  }
}
</script>
