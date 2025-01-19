import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SearchConfig, SearchFormData } from '@/types/ConfigTypes';
import { Plus, Trash2, Edit, PauseCircle, PlayCircle, Copy } from 'lucide-react';
import SearchConfigForm from './SearchConfig';

const defaultFilters = {
    location: '',
    maxPrice: 0,
    minSize: 0,
    dateRange: '',
    propertyTypes: [],
    rentTypes: [],
    wgTypes: [],
    districts: [],
    gender: 'egal',
    smoking: 'egal'
};

const SearchList: React.FC<{
    searches: SearchConfig[];
    onEdit: (id: string) => void;
    onToggleActive: (id: string) => void;
    onDelete: (id: string) => void;
    onDuplicate: (id: string) => void;
}> = ({
    searches,
    onEdit,
    onToggleActive,
    onDelete,
    onDuplicate
}) => (
        <div className="space-y-6 p-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Search Management</h2>
                <Button
                    className="flex items-center gap-2"
                    onClick={() => onEdit('new')}
                >
                    <Plus className="h-4 w-4" />
                    New Search
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Active Searches</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {searches.map((search) => (
                        <Card key={search.id} className="hover:bg-gray-50">
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-2 flex-1">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-semibold text-lg">{search.name}</h3>
                                            <span className={`px-2 py-1 rounded-full text-xs ${search.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                {search.active ? 'Active' : 'Paused'}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                            <div>
                                                <p>Location: {search.filters.location}</p>
                                                <p>Price: up to €{search.filters.maxPrice}</p>
                                                {search.filters.propertyTypes?.length > 0 && (
                                                    <p>Types: {search.filters.propertyTypes.length} selected</p>
                                                )}
                                            </div>
                                            <div>
                                                <p>Size: min {search.filters.minSize}m²</p>
                                                <p>Date Range: {search.filters.dateRange}</p>
                                                {search.filters.districts?.length > 0 && (
                                                    <p>Districts: {search.filters.districts.length} selected</p>
                                                )}
                                            </div>
                                        </div>
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
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onEdit(search.id)}
                                        >
                                            <Edit className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onToggleActive(search.id)}
                                        >
                                            {search.active ? (
                                                <PauseCircle className="h-4 w-4" />
                                            ) : (
                                                <PlayCircle className="h-4 w-4" />
                                            )}
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onDuplicate(search.id)}
                                            title="Duplicate search"
                                        >
                                            <Copy className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onDelete(search.id)}
                                        >
                                            <Trash2 className="h-4 w-4" />
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

const SearchView: React.FC = () => {
    const navigate = useNavigate();
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
                propertyTypes: ['0'],
                rentTypes: ['2'],
                wgTypes: ['6', '12'],
                districts: ['2114'],
                gender: 'egal',
                smoking: 'egal'
            },
            stats: {
                totalFound: 24,
                newListings: 3,
                lastRun: '5 minutes ago',
            },
        },
    ]);

    const handleSaveSearch = (data: SearchFormData) => {
        if (data.id) {
            // Editing existing search
            setSearches(prev =>
                prev.map(search => {
                    if (search.id === data.id) {
                        return {
                            ...search,
                            name: data.name,
                            filters: {
                                location: data.location,
                                maxPrice: parseInt(data.maxPrice) || 0,
                                minSize: parseInt(data.minSize) || 0,
                                dateRange: `${data.dateFrom} - ${data.dateTo}`,
                                propertyTypes: data.propertyTypes,
                                rentTypes: data.rentTypes,
                                wgTypes: data.wgTypes,
                                districts: data.districts,
                                gender: data.gender,
                                smoking: data.smoking,
                            },
                        };
                    }
                    return search;
                })
            );
        } else {
            // Creating new search
            const newSearch: SearchConfig = {
                id: String(searches.length + 1),
                name: data.name,
                active: true,
                filters: {
                    ...defaultFilters,
                    location: data.location,
                    maxPrice: parseInt(data.maxPrice) || 0,
                    minSize: parseInt(data.minSize) || 0,
                    dateRange: `${data.dateFrom} - ${data.dateTo}`,
                    propertyTypes: data.propertyTypes,
                    rentTypes: data.rentTypes,
                    wgTypes: data.wgTypes,
                    districts: data.districts,
                    gender: data.gender,
                    smoking: data.smoking,
                },
                stats: {
                    totalFound: 0,
                    newListings: 0,
                    lastRun: 'Never',
                },
            };
            setSearches(prev => [...prev, newSearch]);
        }
        navigate('/search');
    };

    const handleEdit = (searchId: string) => {
        if (searchId === 'new') {
            navigate('/search/new');
        } else {
            navigate(`/search/edit/${searchId}`);
        }
    };

    const handleToggleActive = (searchId: string) => {
        setSearches(prev =>
            prev.map(search =>
                search.id === searchId
                    ? { ...search, active: !search.active }
                    : search
            )
        );
    };

    const handleDelete = (searchId: string) => {
        setSearches(prev => prev.filter(search => search.id !== searchId));
    };

    const handleDuplicate = (searchId: string) => {
        const searchToDuplicate = searches.find(s => s.id === searchId);
        if (searchToDuplicate) {
            const newSearch = {
                ...searchToDuplicate,
                id: String(searches.length + 1),
                name: `${searchToDuplicate.name} (Copy)`,
                active: false // Start as inactive to avoid duplicate running searches
            };
            setSearches(prev => [...prev, newSearch]);
        }
    };

    const EditSearchRoute = () => {
        const { id } = useParams();
        const searchToEdit = searches.find((s) => s.id === id) || null;

        return (
            <SearchConfigForm
                onBack={() => navigate('/search')}
                onSave={handleSaveSearch}
                initialData={searchToEdit}
                existingSearches={searches}
            />
        );
    };

    return (
        <Routes>
            <Route
                path="/"
                element={
                    <SearchList
                        searches={searches}
                        onEdit={handleEdit}
                        onToggleActive={handleToggleActive}
                        onDelete={handleDelete}
                        onDuplicate={handleDuplicate}
                    />
                }
            />
            <Route
                path="/new"
                element={
                    <SearchConfigForm
                        onBack={() => navigate('/search')}
                        onSave={handleSaveSearch}
                        initialData={null}
                        existingSearches={searches}
                    />
                }
            />
            <Route path="/edit/:id" element={<EditSearchRoute />} />
        </Routes>
    );
};

export default SearchView;