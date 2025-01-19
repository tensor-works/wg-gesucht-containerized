// src/components/HomeView.tsx
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { MessageSquare, Settings, Eye, Send } from 'lucide-react';

interface ListingData {
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

interface HomeViewProps {
    listings: ListingData[];
    setListings: React.Dispatch<React.SetStateAction<ListingData[]>>;
}

const HomeView: React.FC<HomeViewProps> = ({ listings, setListings }) => {
    const [selectedListing, setSelectedListing] = React.useState<number | null>(null);

    return (
        <div className="container mx-auto p-4">
            <Card className="mb-4">
                <CardHeader>
                    <CardTitle className="text-xl font-bold">WG-Gesucht Bot Development UI</CardTitle>
                </CardHeader>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Listings Panel */}
                <Card className="h-full">
                    <CardHeader>
                        <CardTitle>Available Listings</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {listings.map((listing, index) => (
                                <Card
                                    key={index}
                                    className={`cursor-pointer hover:bg-gray-50 ${selectedListing === index ? 'border-blue-500 border-2' : ''}`}
                                    onClick={() => setSelectedListing(index)}
                                >
                                    <CardContent className="p-4">
                                        <h3 className="font-semibold">{listing.user_name}</h3>
                                        <p className="text-sm text-gray-600">{listing.address}</p>
                                        <div className="flex gap-2 mt-2">
                                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                                {listing.wg_type}
                                            </span>
                                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                                                {listing.rental_length_months} months
                                            </span>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Details Panel */}
                <Card className="h-full">
                    <CardHeader>
                        <CardTitle>Listing Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {selectedListing !== null ? (
                            <Tabs defaultValue="listing">
                                <TabsList>
                                    <TabsTrigger value="listing">Listing Text</TabsTrigger>
                                    <TabsTrigger value="gpt">GPT Analysis</TabsTrigger>
                                    <TabsTrigger value="message">Message Preview</TabsTrigger>
                                </TabsList>

                                <TabsContent value="listing">
                                    <div className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                                        {listings[selectedListing].listingText}
                                    </div>
                                </TabsContent>

                                <TabsContent value="gpt">
                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="font-semibold mb-2">Detected Language</h4>
                                            <p>{listings[selectedListing].gptResponse.language}</p>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold mb-2">Detected Keyword</h4>
                                            <p>{listings[selectedListing].gptResponse.keyword}</p>
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="message">
                                    <div className="space-y-4">
                                        <div className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                                            {listings[selectedListing].gptResponse.message}
                                        </div>
                                        <Button className="w-full flex items-center justify-center gap-2">
                                            <Send size={16} />
                                            Send Message
                                        </Button>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        ) : (
                            <div className="text-center text-gray-500 py-8">
                                Select a listing to view details
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default HomeView;