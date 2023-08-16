import {SubscriptionsState} from "@/store/subscriptions/state";
import {getStoreAccessors} from "typesafe-vuex";
import {State} from "@/store/state";

export const getters = {
    subscriptionSearchResults: (state: SubscriptionsState) => state.searchResults,
};

const {read} = getStoreAccessors<SubscriptionsState, State>('');

export const readSubscriptionSearchResults = read(getters.subscriptionSearchResults);
