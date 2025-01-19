// types.ts
export interface SearchConfig {
    id: string;
    name: string;
    active: boolean;
    filters: {
        location: string;
        maxPrice: number;
        minSize: number;
        dateRange: string;
        propertyTypes: string[];  // Added this
        rentTypes: string[];      // Added this
        wgTypes: string[];        // Added this
        districts: string[];      // Added this
        gender: string;           // Added this
        smoking: string;          // Added this
    };
    stats: {
        totalFound: number;
        newListings: number;
        lastRun: string;
    };
}
export interface SearchFormData {
    id?: string; // Optional for new searches
    name: string;
    location: string;
    propertyTypes: string[];
    rentTypes: string[];
    dateFrom: string;
    dateTo: string;
    districts: string[];
    minPrice: string;
    maxPrice: string;
    minSize: string;
    maxSize: string;
    wgTypes: string[];
    gender: string;
    smoking: string;
    ageMin: string;
    ageMax: string;
    onlyWithImages: boolean;
    excludeContactedAds: boolean;
}
