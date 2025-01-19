import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { SearchConfig, SearchFormData } from '@/types/ConfigTypes';
import { Save, ArrowLeft } from 'lucide-react';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';

// Constants remain the same as in your original code
const PROPERTY_TYPES = [
    { id: '0', label: 'WG-Zimmer' },
    { id: '1', label: '1-Zimmer-Wohnung' },
    { id: '2', label: 'Wohnung' },
    { id: '3', label: 'Haus' },
] as const;

const RENT_TYPES = [
    { id: '2', label: 'Unbefristet' },
    { id: '1', label: 'Befristet' },
    { id: '3', label: 'Übernachtung' },
] as const;

const WG_TYPES = [
    { id: '6', label: 'Berufstätigen-WG' },
    { id: '12', label: 'gemischte WG' },
    { id: '1', label: 'Studenten-WG' },
    { id: '11', label: 'keine Zweck-WG' },
    { id: '0', label: 'Zweck-WG' },
    { id: '2', label: 'Frauen-WG' },
    { id: '19', label: 'Internationals welcome' },
    { id: '16', label: 'LGBTQIA+' },
    { id: '4', label: 'Business-WG' },
    { id: '15', label: 'Vegetarisch/Vegan' },
] as const;

const DISTRICTS = [
    { id: '2113', name: 'Allach-Untermenzing' },
    { id: '2114', name: 'Altstadt-Lehel' },
    { id: '2116', name: 'Au-Haidhausen' },
    { id: '2117', name: 'Berg am Laim' },
    { id: '2118', name: 'Bogenhausen' },
    { id: '2119', name: 'Feldmoching-Hasenbergl' },
    { id: '111654', name: 'Laim' },
    { id: '2123', name: 'Ludwigsvorstadt-Isarvorstadt' },
    { id: '2124', name: 'Maxvorstadt' },
] as const;

const GENDER_OPTIONS = [
    { value: 'egal', label: 'Egal' },
    { value: '1', label: 'Mann' },
    { value: '2', label: 'Frau' },
    { value: '3', label: 'Divers' },
] as const;

const SMOKING_OPTIONS = [
    { value: 'egal', label: 'Egal' },
    { value: '1', label: 'Ja' },
    { value: '2', label: 'Nein' },
] as const;

interface SearchConfigFormProps {
    onBack: () => void;
    onSave: (data: SearchFormData) => void;
    initialData: SearchConfig | null;
    existingSearches: SearchConfig[];
}

const SearchConfigForm: React.FC<SearchConfigFormProps> = ({ onBack, onSave, initialData, existingSearches }) => {
    // Helper function to generate next available default name
    const generateDefaultName = () => {
        const baseText = "Your Search";
        let counter = 1;
        let proposedName = `${baseText} ${counter}`;

        while (existingSearches.some(search => search.name === proposedName)) {
            counter++;
            proposedName = `${baseText} ${counter}`;
        }

        return proposedName;
    };

    const [formData, setFormData] = useState<SearchFormData>({
        id: initialData?.id,  // Add the id from initialData
        name: initialData?.name || generateDefaultName(),
        location: initialData?.filters?.location || '',
        propertyTypes: initialData?.filters?.propertyTypes || [],
        rentTypes: initialData?.filters?.rentTypes || [],
        dateFrom: initialData?.filters?.dateRange?.split(' - ')[0] || '',
        dateTo: initialData?.filters?.dateRange?.split(' - ')[1] || '',
        districts: initialData?.filters?.districts || [],
        minPrice: initialData?.filters?.maxPrice?.toString() || '',
        maxPrice: initialData?.filters?.maxPrice?.toString() || '',
        minSize: initialData?.filters?.minSize?.toString() || '',
        maxSize: '',
        wgTypes: initialData?.filters?.wgTypes || [],
        gender: initialData?.filters?.gender || '',
        smoking: initialData?.filters?.smoking || '',
        ageMin: '',
        ageMax: '',
        onlyWithImages: false,
        excludeContactedAds: false,
    });

    const handleSelectAll = (field: keyof SearchFormData, allItems: readonly { id: string }[]) => {
        setFormData((prev) => {
            const currentField = prev[field] as string[];
            if (Array.isArray(currentField)) {
                return {
                    ...prev,
                    [field]: currentField.length === allItems.length ? [] : [...allItems],
                };
            }
            return prev;
        });
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
    };

    // Common checkbox group component
    const CheckboxGroup = ({
        title,
        items,
        fieldName,
        itemLabel = 'label',
        gridCols = 'grid-cols-2'
    }: {
        title: string;
        items: readonly { id: string;[key: string]: string }[];
        fieldName: keyof SearchFormData;
        itemLabel?: string;
        gridCols?: string;
    }) => (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="flex items-center space-x-2 mb-6">
                    <Checkbox
                        id={`select-all-${fieldName}`}
                        checked={Array.isArray(formData[fieldName]) && (formData[fieldName] as string[]).length === items.length}
                        onCheckedChange={() =>
                            handleSelectAll(
                                fieldName,
                                items
                            )
                        }
                    />
                    <Label htmlFor={`select-all-${fieldName}`}>Select All</Label>
                </div>
                <div className={`grid ${gridCols} gap-4`}>
                    {items.map((item) => (
                        <div key={item.id} className="flex items-center space-x-2">
                            <Checkbox
                                id={item.id}
                                checked={Array.isArray(formData[fieldName]) && (formData[fieldName] as string[]).includes(item.id)}
                                onCheckedChange={(checked: boolean) => {
                                    setFormData((prev) => ({
                                        ...prev,
                                        [fieldName]: checked
                                            ? [...(Array.isArray(prev[fieldName]) ? prev[fieldName] as string[] : []), item.id]
                                            : (Array.isArray(prev[fieldName]) ? prev[fieldName] as string[] : []).filter((id: string) => id !== item.id)
                                    }));
                                }}
                            />
                            <Label htmlFor={item.id}>{item[itemLabel]}</Label>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Navigation Buttons */}
            <div className="flex justify-between items-center">
                <Button type="button" variant="outline" onClick={onBack} className="flex items-center gap-2">
                    <ArrowLeft className="h-4 w-4" />
                    Back
                </Button>
                <Button type="submit" className="flex items-center gap-2">
                    <Save className="h-4 w-4" />
                    Save Search
                </Button>
            </div>

            {/* Basic Information */}
            <Card>
                <CardHeader>
                    <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Search Name</Label>
                        <Input
                            value={formData.name}
                            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                            placeholder="Name your search"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>City</Label>
                        <Input
                            value={formData.location}
                            onChange={(e) => setFormData((prev) => ({ ...prev, location: e.target.value }))}
                            placeholder="Enter city"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Property Types */}
            <CheckboxGroup
                title="Property Types"
                items={PROPERTY_TYPES}
                fieldName="propertyTypes"
            />

            {/* Rent Types */}
            <CheckboxGroup
                title="Rent Types"
                items={RENT_TYPES}
                fieldName="rentTypes"
            />

            {/* WG Types */}
            <CheckboxGroup
                title="WG Types"
                items={WG_TYPES}
                fieldName="wgTypes"
            />

            {/* Districts */}
            <CheckboxGroup
                title="Districts"
                items={DISTRICTS}
                fieldName="districts"
                itemLabel="name"
                gridCols="grid-cols-2 md:grid-cols-3"
            />

            {/* Gender and Smoking */}
            <Card>
                <CardHeader>
                    <CardTitle>Personal Preferences</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Gender Preference</Label>
                            <Select
                                value={formData.gender || 'egal'}
                                onValueChange={(value) => setFormData((prev) => ({ ...prev, gender: value }))}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select gender preference" />
                                </SelectTrigger>
                                <SelectContent>
                                    {GENDER_OPTIONS.map((option) => (
                                        <SelectItem key={option.value} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Smoking Preference</Label>
                            <Select
                                value={formData.smoking || 'egal'}
                                onValueChange={(value) => setFormData((prev) => ({ ...prev, smoking: value }))}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select smoking preference" />
                                </SelectTrigger>
                                <SelectContent>
                                    {SMOKING_OPTIONS.map((option) => (
                                        <SelectItem key={option.value} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </form>
    );
};

export default SearchConfigForm;