<template>
  <v-container fluid>
    <v-card class="ma-3 pa-3">
      <v-card-title primary-title>
        <div class="headline primary--text">Create Subscription</div>
      </v-card-title>
      <v-card-text>
        <div class="body-1">
          <p>
            Enter a search term in the box below to see a sample of (non-summarized)
            articles. Once satisfied with the articles produced by your search term, create the subscription.
            Each morning at 9am EST, Bot-Letter will perform the search, summarize the top 5 most relevant articles,
            and send you an email.
          </p>
          <v-alert style="background: antiquewhite">
            <p>
              ⚠️ Please note that this service uses
              <a href="https://newsdata.io/search-news">NewsData.io</a> to retrieve the
              articles. Due to API limitations, you are allowed to perform
              a maximum of 10 searches per day via this website. However, you can use
              their website to perfect your search term before returning here and
              creating the subscription.
            </p>
          </v-alert>
          <v-alert style="background: powderblue">
            <p>
              You can also take a look at their advanced search tips to learn how to
              craft the optimal search term. For example, if your search term is composed of multiple
              words, use quotation marks to search for the exact phrase. E.g. <b>"space industry"</b>.
            </p>
          </v-alert>
        </div>
      </v-card-text>
      <v-card-text>
        <template>
          <v-form
            v-model="valid"
            ref="form"
            lazy-validation
          >
            <v-text-field
              label="Search Term"
              v-model="searchTerm"
              required
            ></v-text-field>
          </v-form>
        </template>
        <p>{{remainingSubscriptionSearches}} remaining searches for the day</p>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="search" :disabled="!valid || remainingSubscriptionSearches == 0">Search</v-btn>
        <v-btn @click="submit" :disabled="subscriptionSearchResults.total_results_count == 0">Create</v-btn>
        <v-btn to="/main/dashboard">Cancel</v-btn>
      </v-card-actions>
      <v-card-text v-if="subscriptionSearchResults.total_results_count != 0">
        Total results: {{ subscriptionSearchResults.total_results_count }}
      </v-card-text>
      <v-card-text v-if="subscriptionSearchResults.total_results_count != 0">
        <h2>{{ subscriptionSearchResults.results.length }} most recent results</h2>
      </v-card-text>
      <v-card class="ma-3 pa-3" v-for="searchResult in subscriptionSearchResults.results">
        <v-card-text>
          <h3>{{searchResult.title}}</h3>
          <p>Article description:</p>
          <p>{{searchResult.description}}</p>
        </v-card-text>
      </v-card>
    </v-card>
  </v-container>
</template>

<!--create the script-->
<script lang="ts">
import {Component} from 'vue-property-decorator';
import {AdaptedVue} from "@/adaptedVue";
import {ISubscriptionSearch, ISubscriptionSearchResults} from "@/interfaces";
import {dispatchSubscriptionCreate, dispatchSubscriptionSearch} from "@/store/subscriptions/actions";
import {readSubscriptionSearchResults} from "@/store/subscriptions/getters";
import {commitClearSubscriptionSearchResults} from "@/store/subscriptions/mutations";
import {
  dispatchCheckCanCreateSubscriptions,
  dispatchCheckRemainingSubscriptionSearches,
  dispatchGetUserProfile
} from "@/store/main/actions";
import {readRemainingSubscriptionSearches} from "@/store/main/getters";

@Component
export default class CreateSubscription extends AdaptedVue {
  public valid = true;
  public searchTerm: string = '';

  get remainingSubscriptionSearches(): number {
    return readRemainingSubscriptionSearches(this.$store);
  }

  public async search() {
    if ((this.$refs.form as any).validate()) {
      const subscriptionSearch: ISubscriptionSearch = {
        search_term: this.searchTerm,
      };
      await dispatchSubscriptionSearch(this.$store, subscriptionSearch);
    }
    await dispatchCheckRemainingSubscriptionSearches(this.$store);
  }

  public async submit() {
    if ((this.$refs.form as any).validate()) {
      commitClearSubscriptionSearchResults(this.$store);
      await dispatchSubscriptionCreate(this.$store, this.searchTerm);
      if (this.$route.path != '/main/dashboard') {
        this.$router.adaptedPush('/main/dashboard');
      }
    }
  }

  get subscriptionSearchResults(): ISubscriptionSearchResults {
    return readSubscriptionSearchResults(this.$store);
  }

  public beforeRouteLeave(to: any, from: any, next: any) {
    commitClearSubscriptionSearchResults(this.$store);
    dispatchGetUserProfile(this.$store);
    dispatchCheckCanCreateSubscriptions(this.$store);
    dispatchCheckRemainingSubscriptionSearches(this.$store);
    next();
  }
}
</script>

<style scoped>

</style>