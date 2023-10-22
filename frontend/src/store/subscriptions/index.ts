import {SubscriptionsState} from "@/store/subscriptions/state";
import {actions} from "@/store/subscriptions/actions";

const defaultState: SubscriptionsState = {
}

export const subscriptionsModule = {
    state: defaultState,
    actions,
}
