import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Eye, Edit, PauseCircle, PlayCircle, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SearchConfig {
    id: string;
    name: string;
    active: boolean;
    filters: {
        location: string;
        maxPrice: number;
        minSize: number;
        dateRange: string;
    };
    stats: {
        totalFound: number;
        newListings: number;
        lastRun: string;
    };
}

const AutomateListView: React.FC = () => {
    const [searches, setSearches] = useState<SearchConfig[]>([
        {
            id: '1',
            name: 'Berlin - Mitte',
            active: true,
            filters: {
                location: 'Mitte, Berlin',
                maxPrice: 800,
                minSize: 15,
                dateRange: '01.03.2024 - 01.04.2024',
            },
            stats: {
                totalFound: 24,
                newListings: 3,
                lastRun: '5 minutes ago',
            },
        },
        {
            id: '2',
            name: 'Berlin - Kreuzberg',
            active: false,
            filters: {
                location: 'Kreuzberg, Berlin',
                maxPrice: 900,
                minSize: 18,
                dateRange: '01.03.2024 - 01.04.2024',
            },
            stats: {
                totalFound: 16,
                newListings: 0,
                lastRun: '15 minutes ago',
            },
        },
    ]);

    const navigate = useNavigate();

    return (
        <div className="space-y-6 p-6">
            {/* Header with Add Search button */}
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Automation Management</h2>
                <Button className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    New Automation
                </Button>
            </div>

            {/* Active Searches */}
            <Card>
                <CardHeader>
                    <CardTitle>Active Automations</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {searches.map((search) => (
                        <Card
                            key={search.id}
                            className="hover:bg-gray-50 cursor-pointer"
                            onClick={() => navigate(`/automate/${search.id}`)} // Navigate to the subpage
                        >
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between">
                                    {/* Search Info */}
                                    <div className="space-y-2 flex-1">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-semibold text-lg">{search.name}</h3>
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs ${search.active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                    }`}
                                            >
                                                {search.active ? 'Active' : 'Paused'}
                                            </span>
                                        </div>

                                        {/* Search Details */}
                                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                            <div>
                                                <p>Location: {search.filters.location}</p>
                                                <p>Price: up to €{search.filters.maxPrice}</p>
                                            </div>
                                            <div>
                                                <p>Size: min {search.filters.minSize}m²</p>
                                                <p>Date Range: {search.filters.dateRange}</p>
                                            </div>
                                        </div>

                                        {/* Stats */}
                                        <div className="flex gap-4 text-sm mt-3">
                                            <span className="text-blue-600">
                                                {search.stats.totalFound} total listings
                                            </span>
                                            {search.stats.newListings > 0 && (
                                                <span className="text-green-600">
                                                    {search.stats.newListings} new
                                                </span>
                                            )}
                                            <span className="text-gray-500">
                                                Last run: {search.stats.lastRun}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2">
                                        <Button variant="outline" size="sm">
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                        <Button variant="outline" size="sm">
                                            <Edit className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={(e) => {
                                                e.stopPropagation(); // Prevent triggering navigation
                                                setSearches(
                                                    searches.map((s) =>
                                                        s.id === search.id
                                                            ? { ...s, active: !s.active }
                                                            : s
                                                    )
                                                );
                                            }}
                                        >
                                            {search.active ? (
                                                <PauseCircle className="h-4 w-4" />
                                            ) : (
                                                <PlayCircle className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </CardContent>
            </Card>
        </div>
    );
};

export default AutomateListView;
