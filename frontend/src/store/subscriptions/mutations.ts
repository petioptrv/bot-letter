import {getStoreAccessors} from "typesafe-vuex";
import {State} from "@/store/state";
import {SubscriptionsState} from "@/store/subscriptions/state";
import {ISubscriptionSearchResults} from "@/interfaces";

export const mutations = {
    setSubscriptionSearchResults(state: SubscriptionsState, payload: ISubscriptionSearchResults) {
        state.searchResults = payload;
    },
    clearSubscriptionSearchResults(state: SubscriptionsState) {
        state.searchResults = {results_count: 0, results: []};
    },
};

const {commit} = getStoreAccessors<SubscriptionsState | any, State>('');

export const commitSetSubscriptionSearchResults = commit(mutations.setSubscriptionSearchResults);
export const commitClearSubscriptionSearchResults = commit(mutations.clearSubscriptionSearchResults);
