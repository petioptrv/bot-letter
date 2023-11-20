import {ActionContext} from "vuex";
import {State} from "@/store/state";
import {SubscriptionsState} from "@/store/subscriptions/state";
import {api} from "@/api";
import {commitAddNotification} from "@/store/main/mutations";
import {AxiosError} from "axios";
import {dispatchCheckApiError} from "@/store/main/actions";
import {getStoreAccessors} from "typesafe-vuex";
import {ISubscription} from "@/interfaces";

type SubscriptionsContext = ActionContext<SubscriptionsState, State>;

interface ErrorResponse {
  detail: string;
}

export const actions = {
    async actionSubscriptionCreate(context: SubscriptionsContext, searchTerm: string) {
        try {
            await api.postSubscriptionCreate(context.rootState.main.token, searchTerm);
            const creationNotification = { content: 'subscription created', showProgress: false };
            commitAddNotification(context, creationNotification);
        } catch (error) {
            const axiosError = error as AxiosError;
            await dispatchCheckApiError(context, axiosError);

            let errorMessage = 'An error occurred';
            if (axiosError.response && axiosError.response.data) {
                const errorData = axiosError.response.data as ErrorResponse;
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            }
            const errorNotification = {
                content: errorMessage,
                color: 'error',
                showProgress: false
            };
            commitAddNotification(context, errorNotification);
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
    },
    async actionSubscriptionIssue(context: SubscriptionsContext, subscription: ISubscription) {
        try {
            await api.postSubscriptionIssue(context.rootState.main.token, subscription);
            const searchingNotification = { content: 'subscription issued', showProgress: false };
            commitAddNotification(context, searchingNotification);
        } catch (error) {
            await dispatchCheckApiError(context, error as AxiosError);
        }
    }
};

const {dispatch} = getStoreAccessors<SubscriptionsState, State>('');

export const dispatchSubscriptionCreate = dispatch(actions.actionSubscriptionCreate);
export const dispatchSubscriptionDelete = dispatch(actions.actionSubscriptionDelete);
export const dispatchSubscriptionIssue = dispatch(actions.actionSubscriptionIssue);
