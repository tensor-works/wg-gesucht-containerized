export interface ListingData {
    ref: string;
    user_name: string;
    address: string;
    wg_type: string;
    rental_length_months: number;
    rental_start: Date;
    listingText: string;
    gptResponse: {
        language: string;
        keyword: string;
        message: string;
    };
}
