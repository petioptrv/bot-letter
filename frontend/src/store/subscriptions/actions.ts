import {ActionContext} from "vuex";
import {State} from "@/store/state";
import {SubscriptionsState} from "@/store/subscriptions/state";
import {api} from "@/api";
import {commitAddNotification, commitRemoveNotification} from "@/store/main/mutations";
import {AxiosError} from "axios";
import {dispatchCheckApiError} from "@/store/main/actions";
import {getStoreAccessors} from "typesafe-vuex";
import {ISubscription, ISubscriptionSearch} from "@/interfaces";
import {commitSetSubscriptionSearchResults} from "@/store/subscriptions/mutations";


type SubscriptionsContext = ActionContext<SubscriptionsState, State>;

export const actions = {
    async actionSubscriptionSearch(context: SubscriptionsContext, payload: ISubscriptionSearch) {
        try {
            const searchingNotification = { content: 'searching', showProgress: true };
            commitAddNotification(context, searchingNotification);
            const response = (await Promise.all([
                api.getSubscriptionSearch(context.rootState.main.token, payload),
                await new Promise<void>((resolve, reject) => setTimeout(() => resolve(), 500)),
            ]))[0];
            commitRemoveNotification(context, searchingNotification);
            commitSetSubscriptionSearchResults(context, response.data);
        } catch (error) {
            await dispatchCheckApiError(context, error as AxiosError);
        }
    },
    async actionSubscriptionCreate(context: SubscriptionsContext, searchTerm: string) {
        try {
            await api.postSubscriptionCreate(context.rootState.main.token, searchTerm);
            const searchingNotification = { content: 'subscription created', showProgress: false };
            commitAddNotification(context, searchingNotification);
        } catch (error) {
            await dispatchCheckApiError(context, error as AxiosError);
        }
    },
    async actionSubscriptionDelete(context: SubscriptionsContext, subscription: ISubscription) {
        try {
            await api.deleteSubscription(context.rootState.main.token, subscription);
            const searchingNotification = { content: 'subscription deleted', showProgress: false };
            commitAddNotification(context, searchingNotification);
        } catch (error) {
            await dispatchCheckApiError(context, error as AxiosError);
        }
    }
};

const {dispatch} = getStoreAccessors<SubscriptionsState, State>('');

export const dispatchSubscriptionSearch = dispatch(actions.actionSubscriptionSearch);
export const dispatchSubscriptionCreate = dispatch(actions.actionSubscriptionCreate);
export const dispatchSubscriptionDelete = dispatch(actions.actionSubscriptionDelete);
