import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
    Send,
    Plus,
    CheckCircle,
    List,
    XCircle,
    Settings,
    ChevronDown,
    ChevronRight,
    Wand2
} from 'lucide-react';

interface Listing {
    id: string;
    title: string;
    address: string;
    description: string;
    listingText: string;
    preparedMessage?: string;
}

interface Search {
    id: string;
    name: string;
    listings: Listing[];
    settings: {
        autoPrepare: boolean;
        autoSend: boolean;
        defaultGPTModel: string;
        messageDelay: number;
    };
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
                listingText: 'Detailed listing description with all requirements and preferences...'
            },
            {
                id: '102',
                title: 'Bright Apartment in Mitte',
                address: 'Hackescher Markt, Berlin-Mitte',
                description: 'Bright and spacious apartment in the heart of Mitte...',
                listingText: 'Another detailed listing with specific requirements...'
            },
        ],
        settings: {
            autoPrepare: false,
            autoSend: false,
            defaultGPTModel: 'gpt-3.5-turbo',
            messageDelay: 60,
        },
        doList: ['Be friendly', 'Mention the great location'],
        dontList: ['Avoid discussing the price'],
    });

    const [selectedListingId, setSelectedListingId] = useState<string | null>(null);
    const [messageEditorContent, setMessageEditorContent] = useState('');
    const [chatInput, setChatInput] = useState('');
    const [chatMessages, setChatMessages] = useState<{ role: string; message: string }[]>([]);
    const [selectedGPTModel, setSelectedGPTModel] = useState('gpt-3.5-turbo');
    const [doItem, setDoItem] = useState('');
    const [dontItem, setDontItem] = useState('');
    const [showRules, setShowRules] = useState(true);
    const [showSettings, setShowSettings] = useState(false);

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

    const handleAddDo = () => {
        if (doItem) {
            setSearch({
                ...search,
                doList: [...search.doList, doItem]
            });
            setDoItem('');
        }
    };

    const handleAddDont = () => {
        if (dontItem) {
            setSearch({
                ...search,
                dontList: [...search.dontList, dontItem]
            });
            setDontItem('');
        }
    };

    const handleSendChatMessage = () => {
        if (chatInput.trim()) {
            setChatMessages([...chatMessages, { role: 'user', message: chatInput }]);
            setChatInput('');

            setTimeout(() => {
                setChatMessages((prev) => [
                    ...prev,
                    { role: 'bot', message: 'This is a simulated response from the bot.' },
                ]);
            }, 1000);
        }
    };

    const handleCorrectTemplate = () => {
        alert('Request sent to LLM to correct the template content!');
    };

    const updateSettings = (key: keyof Search['settings'], value: unknown) => {
        setSearch({
            ...search,
            settings: {
                ...search.settings,
                [key]: value
            }
        });
    };

    return (
        <div className="flex h-full">
            {/* Left Pane: Listings and Rules */}
            <div className="w-1/4 p-4 border-r bg-gray-50 space-y-4">
                {/* Settings Button */}
                <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-lg">{search.name}</h3>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowSettings(!showSettings)}
                    >
                        <Settings className="h-4 w-4" />
                    </Button>
                </div>

                {/* Settings Panel */}
                {showSettings && (
                    <Card className="mb-4">
                        <CardHeader>
                            <CardTitle className="text-base">Automation Settings</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Auto-prepare messages</span>
                                <Switch
                                    checked={search.settings.autoPrepare}
                                    onCheckedChange={(checked: boolean) => updateSettings('autoPrepare', checked)}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Auto-send messages</span>
                                <Switch
                                    checked={search.settings.autoSend}
                                    onCheckedChange={(checked: boolean) => updateSettings('autoSend', checked)}
                                />
                            </div>
                            <div className="space-y-2">
                                <span className="text-sm">Default GPT Model</span>
                                <Select
                                    value={search.settings.defaultGPTModel}
                                    onValueChange={(value) => updateSettings('defaultGPTModel', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select GPT Model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <span className="text-sm">Message Delay (seconds)</span>
                                <Input
                                    type="number"
                                    value={search.settings.messageDelay}
                                    onChange={(e) => updateSettings('messageDelay', parseInt(e.target.value))}
                                />
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Listings */}
                <div className="space-y-2">
                    {search.listings.map((listing) => (
                        <Card
                            key={listing.id}
                            onClick={() => {
                                setSelectedListingId(listing.id);
                                if (search.settings.autoPrepare) {
                                    handlePrepareMessage(listing);
                                }
                            }}
                            className={`cursor-pointer ${selectedListingId === listing.id ? 'bg-blue-100' : ''}`}
                        >
                            <CardContent>
                                <h5 className="font-semibold">{listing.title}</h5>
                                <p className="text-sm text-gray-600">{listing.address}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Collapsible Rules Section */}
                <div className="space-y-2">
                    <button
                        className="flex items-center gap-2 text-sm font-semibold w-full"
                        onClick={() => setShowRules(!showRules)}
                    >
                        {showRules ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        Automation Rules
                    </button>

                    {showRules && (
                        <Card>
                            <CardContent className="pt-4">
                                {/* Do List */}
                                <div className="mb-4">
                                    <h4 className="font-semibold mb-2 text-sm">Do List</h4>
                                    <div className="space-y-2">
                                        {search.doList.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-2 text-sm">
                                                <List className="h-4 w-4 text-gray-500" />
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                        <div className="flex gap-2 mt-2">
                                            <Input
                                                value={doItem}
                                                onChange={(e) => setDoItem(e.target.value)}
                                                placeholder="Add an item..."
                                                className="text-sm"
                                            />
                                            <Button size="sm" onClick={handleAddDo}>
                                                <Plus className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>

                                {/* Don't List */}
                                <div>
                                    <h4 className="font-semibold mb-2 text-sm">Don't List</h4>
                                    <div className="space-y-2">
                                        {search.dontList.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-2 text-sm">
                                                <XCircle className="h-4 w-4 text-gray-500" />
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                        <div className="flex gap-2 mt-2">
                                            <Input
                                                value={dontItem}
                                                onChange={(e) => setDontItem(e.target.value)}
                                                placeholder="Add an item..."
                                                className="text-sm"
                                            />
                                            <Button size="sm" onClick={handleAddDont}>
                                                <Plus className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>

            {/* Right Pane: Message Editor and Chat */}
            <div className="w-3/4 p-6 space-y-6">
                {selectedListing ? (
                    <>
                        <h2 className="text-xl font-bold">{selectedListing.title}</h2>

                        {/* Listing Text Display */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Original Listing</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-gray-50 p-4 rounded">
                                    {selectedListing.listingText}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Message Editor */}
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
                                <div className="flex justify-between">
                                    <Button variant="default" onClick={handleCorrectTemplate}>
                                        <CheckCircle className="h-4 w-4 mr-2" />
                                        Correct Template
                                    </Button>
                                    {!search.settings.autoPrepare && !messageEditorContent && (
                                        <Button variant="default" onClick={() => handlePrepareMessage(selectedListing)}>
                                            <Wand2 className="h-4 w-4 mr-2" />
                                            Generate Message
                                        </Button>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Chat with Bot */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Chat with Bot</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {/* Select GPT Model */}
                                <div className="mb-4">
                                    <Select
                                        value={selectedGPTModel}
                                        onValueChange={setSelectedGPTModel}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select GPT Model" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Chat Messages */}
                                <div className="space-y-4 max-h-40 overflow-y-auto border p-3 rounded bg-gray-50 mb-4">
                                    {chatMessages.map((msg, idx) => (
                                        <div
                                            key={idx}
                                            className={`p-2 rounded ${msg.role === 'user' ? 'bg-blue-100 text-blue-800' : 'bg-gray-200'
                                                }`}
                                        >
                                            <strong>{msg.role === 'user' ? 'You' : 'Bot'}:</strong> {msg.message}
                                        </div>
                                    ))}
                                </div>

                                {/* Chat Input */}
                                <div className="flex items-center gap-2">
                                    <Input
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        placeholder="Type your message..."
                                        className="flex-1"
                                    />
                                    <Button onClick={handleSendChatMessage}>
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                ) : (
                    <div className="text-center text-gray-500 py-8">
                        Select a listing to start editing the message
                    </div>
                )}
            </div>
        </div>
    );
};

export default AutomateSubpage;