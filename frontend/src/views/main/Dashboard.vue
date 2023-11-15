<template>
  <v-container fluid>
    <v-card class="ma-3 pa-3">
      <v-card-title primary-title>
        <div class="headline primary--text">Dashboard</div>
      </v-card-title>
      <v-card-text>
        <div class="headline font-weight-light ma-5">Welcome {{ greetedUser }}</div>
      </v-card-text>
      <v-card-actions>
        <v-btn to="/main/profile/view">View Profile</v-btn>
        <v-btn to="/main/profile/edit">Edit Profile</v-btn>
        <v-btn to="/main/profile/password">Change Password</v-btn>
      </v-card-actions>
      <v-card-text>
        <div class="body-1">
          <p>
            Bot-Letter is a DIY newsletter service that allows you to create personalized newsletters.
            You will receive daily emails for each one of your subscriptions with the top 5 most relevant articles from
            the past 24 hours. Each article will be succinctly summarized and ready for your morning read
            (cup of joe sold separately ☕️).
          </p>
          <v-alert style="background: antiquewhite">
            <p>
              ⚠️ Please keep in mind that this service is in the development phase and bugs are expected.
              If you encounter any issues, or have suggestions for improvement, please email
              at <a href="mailto:botletternews@gmail.com">email us</a>.
            </p>
          </v-alert>
        </div>
      </v-card-text>
    </v-card>
    <v-card v-for="(subscription) in userProfileSubscriptions" class="ma-3 pa-3">
      <v-card-title>Subscription</v-card-title>
      <v-card-text>
        <div class="body-1">Search term <b>{{ subscription.newsletter_description }}</b></div>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="issueSubscription(subscription)" class="ml-auto" :disabled="!canIssueSample(subscription)">
          Send Sample
        </v-btn>
        <v-btn @click="deleteSubscription(subscription)">Delete</v-btn>
      </v-card-actions>
    </v-card>
    <v-card v-if="canCreateSubscription" class="ma-3 pa-3">
      <v-card-title>Create New Subscription</v-card-title>
      <v-form ref="form">
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <v-text-field
                label="Newsletter Description"
                v-model="newNewsletterDescription"
                required
                v-bind="attrs"
                v-on="on"
            ></v-text-field>
          </template>
          <span>
            E.g. "I want news about Tesla. I am mostly interested in financial news regarding the company.
            I am not interested in tech-related news."
          </span>
        </v-tooltip>
        <v-btn @click="createSubscription">Create</v-btn>
      </v-form>
    </v-card>
  </v-container>
</template>

<script lang="ts">
import {Component} from 'vue-property-decorator';
import {readCanCreateSubscriptions, readUserProfile} from '@/store/main/getters';
import {ISubscription} from "@/interfaces";
import {AdaptedVue} from "@/adaptedVue";
import {
  dispatchSubscriptionCreate,
  dispatchSubscriptionDelete,
  dispatchSubscriptionIssue
} from "@/store/subscriptions/actions";
import {
  dispatchCheckCanCreateSubscriptions,
  dispatchGetUserProfile
} from "@/store/main/actions";
import {commitAddNotification} from "@/store/main/mutations";

@Component
export default class Dashboard extends AdaptedVue {
  public newNewsletterDescription: string = '';

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

  public canIssueSample(subscription: ISubscription): boolean {
    return subscription.sample_available;
  }

  public async createSubscription() {
    if ((this.$refs.form as any).validate()) {
      if (this.newNewsletterDescription.length < parseInt(process.env.VUE_APP_MIN_NEWSLETTER_DESCRIPTION_LENGTH)) {
        const lengthNotification = {
          content: `Newsletter description must be at least ${process.env.VUE_APP_MIN_NEWSLETTER_DESCRIPTION_LENGTH}
           characters long`,
          color: 'error',
          showProgress: false
        };
        commitAddNotification(this.$store, lengthNotification);
        return;
      } else if (this.newNewsletterDescription.length > parseInt(process.env.VUE_APP_MAX_NEWSLETTER_DESCRIPTION_LENGTH)) {
        const lengthNotification = {
          content: `Newsletter description can be at most ${process.env.VUE_APP_MAX_NEWSLETTER_DESCRIPTION_LENGTH}
           characters long`,
          color: 'error',
          showProgress: false
        };
        commitAddNotification(this.$store, lengthNotification);
        return;
      } else {
        await dispatchSubscriptionCreate(this.$store, this.newNewsletterDescription);
        await dispatchGetUserProfile(this.$store);
        await dispatchCheckCanCreateSubscriptions(this.$store);
        this.newNewsletterDescription = '';
        if (this.$route.path != '/main/dashboard') {
          this.$router.adaptedPush('/main/dashboard');
        }
      }
    }
  }

  public async deleteSubscription(subscription: ISubscription) {
    await dispatchSubscriptionDelete(this.$store, subscription);
    await dispatchGetUserProfile(this.$store);
    await dispatchCheckCanCreateSubscriptions(this.$store);
  }

  public async issueSubscription(subscription: ISubscription) {
    await dispatchSubscriptionIssue(this.$store, subscription);
    await dispatchGetUserProfile(this.$store);
  }
}
</script>
