import {SubscriptionsState} from "@/store/subscriptions/state";
import {mutations} from "@/store/subscriptions/mutations";
import {actions} from "@/store/subscriptions/actions";
import {getters} from "@/store/subscriptions/getters";

const defaultState: SubscriptionsState = {
    searchResults: {
        results_count: 0,
        results: [],
    }
}

export const subscriptionsModule = {
    state: defaultState,
    mutations,
    actions,
    getters,
}
