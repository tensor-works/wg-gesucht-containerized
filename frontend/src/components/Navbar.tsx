import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Search, Bot, MessageSquare, Settings, User } from 'lucide-react';

interface NavbarProps { }

const Navbar: React.FC<NavbarProps> = () => {
    const location = useLocation();

    const isActive = (path: string) =>
        location.pathname === path ? 'text-black border-b-2 border-black' : 'text-gray-500';

    return (
        <div className="w-full border-b bg-white">
            <div className="max-w-7xl mx-auto px-4">
                <div className="flex h-14 items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 bg-blue-600 rounded flex items-center justify-center">
                            <span className="text-white font-bold">WG</span>
                        </div>
                        <span className="font-semibold text-gray-900">WG-Gesucht Bot</span>
                    </div>

                    {/* Navigation Links */}
                    <div className="flex items-center gap-6">
                        <Link to="/" className={`flex items-center ${isActive('/')}`}>
                            <Home className="h-5 w-5 mr-1" />
                            Home
                        </Link>
                        <Link to="/search" className={`flex items-center ${isActive('/search')}`}>
                            <Search className="h-5 w-5 mr-1" />
                            Search
                        </Link>
                        <Link to="/automate" className={`flex items-center ${isActive('/automate')}`}>
                            <Bot className="h-5 w-5 mr-1" />
                            Automate
                        </Link>
                        <Link to="/templates" className={`flex items-center ${isActive('/templates')}`}>
                            <MessageSquare className="h-5 w-5 mr-1" />
                            Templates
                        </Link>
                    </div>

                    {/* Profile Icon with Settings Link */}
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-gray-500 hover:text-black rounded-full hover:bg-gray-100">
                            <Settings className="h-5 w-5" />
                        </button>
                        <Link to="/settings" className="p-1">
                            <div className="h-8 w-8 bg-gray-200 rounded-full flex items-center justify-center">
                                <User className="h-5 w-5 text-gray-600" />
                            </div>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Navbar;
