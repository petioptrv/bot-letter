export interface ISubscription {
    id: number;
    search_term: string;
}

export interface ISubscriptionSearch {
    search_term: string;
}

export interface ISubscriptionSearchResult {
    title: string;
    url: string;
    img_url: string;
    search_term: string;
    publishing_timestamp: number;
    description: string;
    content: string;
}

export interface ISubscriptionSearchResults {
    total_results_count: number;
    results: ISubscriptionSearchResult[];
}

export interface ISubscriptionCreate {
    search_term: string;
}

export interface IUserProfile {
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    full_name: string;
    id: number;
    subscriptions: ISubscription[];
}

export interface IUserProfileUpdate {
    email?: string;
    full_name?: string;
    password?: string;
    is_active?: boolean;
    is_superuser?: boolean;
}

export interface IUserProfileCreate {
    email: string;
    full_name?: string;
    password?: string;
    is_active?: boolean;
    is_superuser?: boolean;
}
