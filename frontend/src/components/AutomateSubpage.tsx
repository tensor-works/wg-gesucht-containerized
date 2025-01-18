import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Send, Plus } from 'lucide-react';

interface Listing {
    id: string;
    title: string;
    address: string;
    description: string;
    preparedMessage?: string;
}

interface Search {
    id: string;
    name: string;
    listings: Listing[];
    autoPrepare: boolean;
    doList: string[];
    dontList: string[];
}

const AutomateSubpage: React.FC = () => {
    const { searchId } = useParams<{ searchId: string }>();

    const [search, setSearch] = useState<Search>({
        id: searchId!,
        name: 'Berlin - Mitte',
        listings: [
            {
                id: '101',
                title: 'Cozy Room in Berlin Mitte',
                address: 'Alexanderplatz, Berlin-Mitte',
                description: 'A cozy and clean room available for rent in Berlin Mitte...',
            },
            {
                id: '102',
                title: 'Bright Apartment in Mitte',
                address: 'Hackescher Markt, Berlin-Mitte',
                description: 'Bright and spacious apartment in the heart of Mitte...',
            },
        ],
        autoPrepare: false,
        doList: ['Be friendly', 'Mention the great location'],
        dontList: ['Avoid discussing the price'],
    });

    const [selectedListingId, setSelectedListingId] = useState<string | null>(null);
    const [gptModel, setGptModel] = useState('gpt-3.5-turbo');
    const [messageEditorContent, setMessageEditorContent] = useState('');

    const selectedListing = search.listings.find((listing) => listing.id === selectedListingId);

    const handlePrepareMessage = (listing: Listing) => {
        const preparedMessage = `Prepared message for "${listing.title}":\n\n${listing.description}`;
        listing.preparedMessage = preparedMessage;
        setMessageEditorContent(preparedMessage);

        setSearch({
            ...search,
            listings: search.listings.map((l) =>
                l.id === listing.id ? { ...l, preparedMessage } : l
            ),
        });
    };

    return (
        <div className="flex h-full">
            {/* Left Pane: Listings */}
            <div className="w-1/4 p-4 border-r bg-gray-50 space-y-4">
                <h3 className="font-semibold text-lg">{search.name}</h3>
                <div className="space-y-2">
                    {search.listings.map((listing) => (
                        <Card
                            key={listing.id}
                            onClick={() => {
                                setSelectedListingId(listing.id);
                                if (search.autoPrepare) {
                                    handlePrepareMessage(listing);
                                }
                            }}
                            className={`cursor-pointer ${selectedListingId === listing.id ? 'bg-blue-100' : ''
                                }`}
                        >
                            <CardContent>
                                <h5 className="font-semibold">{listing.title}</h5>
                                <p className="text-sm text-gray-600">{listing.address}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Right Pane: Automation and Editor */}
            <div className="w-3/4 p-6 space-y-6">
                {selectedListing && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Message Editor</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Textarea
                                value={messageEditorContent}
                                onChange={(e) => setMessageEditorContent(e.target.value)}
                                placeholder="Edit your message here..."
                                className="w-full h-40"
                            />
                            <Select
                                value={gptModel}
                                onValueChange={(value) => setGptModel(value)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select GPT Model" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                                </SelectContent>
                            </Select>
                            <Button variant="default">
                                <Send className="h-4 w-4 mr-2" />
                                Send Message
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
};

export default AutomateSubpage;
