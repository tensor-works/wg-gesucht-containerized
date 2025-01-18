import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomeView from './components/HomeView';
import SearchView from './components/SearchView';
import SettingsView from './components/SettingsView';
import TemplatesView from './components/TemplatesView';
import AutomateListView from './components/AutomateView';
import AutomateSubpage from './components/AutomateSubpage';

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

const MainLayout: React.FC = () => {
  const [listings, setListings] = React.useState<ListingData[]>([
    {
      ref: '/wg-zimmer-in-Berlin-Mitte.123.html',
      user_name: 'John Doe',
      address: 'Alexanderplatz, Berlin-Mitte',
      wg_type: '2er WG',
      rental_length_months: 6,
      rental_start: new Date('2024-03-01'),
      listingText: 'We are looking for a friendly and clean roommate...',
      gptResponse: {
        language: 'German',
        keyword: 'Sauberkeit',
        message: 'Hallo John,\n\nIch habe gesehen dass dir Sauberkeit wichtig ist...',
      },
    },
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto p-6">
        <Routes>
          {/* Route Definitions */}
          <Route
            path="/"
            element={<HomeView listings={listings} setListings={setListings} />}
          />
          <Route path="/search" element={<SearchView />} />
          <Route path="/automate" element={<AutomateListView />} />
          <Route path="/automate/:searchId" element={<AutomateSubpage />} />
          <Route path="/templates" element={<TemplatesView />} />
          <Route path="/settings" element={<SettingsView />} />
        </Routes>
      </div>
    </div>
  );
};

export default MainLayout;
