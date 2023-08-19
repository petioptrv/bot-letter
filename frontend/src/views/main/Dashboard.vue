<template>
  <v-container fluid>
    <v-card class="ma-3 pa-3">
      <v-card-title primary-title>
        <div class="headline primary--text">Dashboard</div>
      </v-card-title>
      <v-card-text>
        <div class="headline font-weight-light ma-5">Welcome {{greetedUser}}</div>
      </v-card-text>
      <v-card-actions>
        <v-btn to="/main/profile/view">View Profile</v-btn>
        <v-btn to="/main/profile/edit">Edit Profile</v-btn>
        <v-btn to="/main/profile/password">Change Password</v-btn>
      </v-card-actions>
      <v-card-text>
        <div class="body-1">
          <p>
            Bot-Letter is a DIY newsletter service that allows you to create personal newsletters based on search terms.
            Each day, you will receive an email with the top 5 most relevant articles from
            the previous day. Each article will be succinctly summarized, and ready for your morning read
            (cup of joe sold separately ☕️).
          </p>
          <v-alert style="background: antiquewhite">
            <p>
              ⚠️ Please keep in mind that this service is in the development phase and bugs are expected.
              If you encounter any issues, or have suggestions for improvement, please
              at <a href="mailto:botletternews@gmail.com">email us</a>.
            </p>
          </v-alert>
        </div>
      </v-card-text>
    </v-card>
    <v-card v-for="(subscription) in userProfileSubscriptions" class="ma-3 pa-3">
      <v-card-title>Subscription</v-card-title>
      <v-card-text>
        <div class="body-1">Search term <b>{{subscription.search_term}}</b></div>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="deleteSubscription(subscription)" class="ml-auto">Delete</v-btn>
      </v-card-actions>
    </v-card>
    <v-card v-if="canCreateSubscription" class="ma-3 pa-3">
      <v-card-title>Create New Subscription</v-card-title>
      <v-btn to="/main/create-subscription">Create</v-btn>
    </v-card>
  </v-container>
</template>

<script lang="ts">
import { Component } from 'vue-property-decorator';
import {readCanCreateSubscriptions, readUserProfile} from '@/store/main/getters';
import {ISubscription} from "@/interfaces";
import {AdaptedVue} from "@/adaptedVue";
import {dispatchSubscriptionDelete} from "@/store/subscriptions/actions";
import {
  dispatchCheckCanCreateSubscriptions,
  dispatchCheckRemainingSubscriptionSearches,
  dispatchGetUserProfile
} from "@/store/main/actions";

@Component
export default class Dashboard extends AdaptedVue {
  get userProfileSubscriptions() {
    const userProfile = readUserProfile(this.$store);
    let subscriptions: ISubscription[] = [];
    if (userProfile) {
      subscriptions = userProfile.subscriptions;
    }
    return subscriptions;
  }

  get greetedUser() {
    const userProfile = readUserProfile(this.$store);
    if (userProfile) {
      if (userProfile.full_name) {
        return userProfile.full_name;
      } else {
        return userProfile.email;
      }
    }
  }

  get canCreateSubscription() {
    return readCanCreateSubscriptions(this.$store);
  }

  public async deleteSubscription(subscription: ISubscription) {
    await dispatchSubscriptionDelete(this.$store, subscription);
    await dispatchGetUserProfile(this.$store);
    await dispatchCheckCanCreateSubscriptions(this.$store);
    await dispatchCheckRemainingSubscriptionSearches(this.$store);
  }
}
</script>
