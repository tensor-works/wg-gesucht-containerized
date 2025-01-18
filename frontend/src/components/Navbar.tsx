import React from 'react';
import { Home, Search, MessageSquare, Settings, User, Bot, LucideIcon } from 'lucide-react';

interface NavItemProps {
    icon: LucideIcon;
    label: string;
    id: string;
}

interface NavbarProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
    const NavItem: React.FC<NavItemProps> = ({ icon: Icon, label, id }) => (
        <button
            onClick={() => onTabChange(id)}
            className={`flex flex-col items-center px-3 py-2 hover:text-black ${activeTab === id
                    ? 'text-black border-b-2 border-black'
                    : 'text-gray-500'
                }`}
        >
            <Icon className="h-5 w-5" />
            <span className="text-xs mt-1">{label}</span>
        </button>
    );

    return (
        <div className="w-full border-b bg-white">
            <div className="max-w-7xl mx-auto px-4">
                <div className="flex h-14 items-center justify-between">
                    {/* Left section - Logo and Bot name */}
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 bg-blue-600 rounded flex items-center justify-center">
                            <span className="text-white font-bold">WG</span>
                        </div>
                        <span className="font-semibold text-gray-900">WG-Gesucht Bot</span>
                    </div>

                    {/* Center section - Main navigation */}
                    <div className="flex items-center">
                        <NavItem icon={Home} label="Home" id="home" />
                        <NavItem icon={Search} label="Search" id="search" />
                        <NavItem icon={Bot} label="Automate" id="automate" />
                        <NavItem icon={MessageSquare} label="Templates" id="templates" />
                    </div>

                    {/* Right section - Gear Icon and Profile */}
                    <div className="flex items-center gap-4">
                        {/* Gear Icon - Placeholder or Extra Settings */}
                        <button
                            onClick={() => alert('Gear icon clicked!')}
                            className="p-2 text-gray-500 hover:text-black rounded-full hover:bg-gray-100"
                        >
                            <Settings className="h-5 w-5" />
                        </button>

                        {/* Profile Icon - Navigates to Settings */}
                        <button
                            onClick={() => onTabChange('settings')}
                            className={`p-1 rounded-full hover:bg-gray-100 ${activeTab === 'settings' ? 'bg-gray-100' : ''
                                }`}
                        >
                            <div
                                className={`h-8 w-8 rounded-full flex items-center justify-center ${activeTab === 'settings'
                                        ? 'bg-blue-100'
                                        : 'bg-gray-200'
                                    }`}
                            >
                                <User
                                    className={`h-5 w-5 ${activeTab === 'settings'
                                            ? 'text-blue-600'
                                            : 'text-gray-600'
                                        }`}
                                />
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Navbar;
