import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Key,
    Mail,
    Bell,
    CreditCard,
    Check,
    AlertCircle,
    Bot,
    Eye,
    EyeOff
} from 'lucide-react';

const ProfileView = () => {
    const [wgGesuchtCredentials, setWgGesuchtCredentials] = useState({
        email: '',
        password: '',
        status: 'disconnected' as 'connected' | 'disconnected'
    });

    const [openAiKey, setOpenAiKey] = useState({
        key: '',
        status: false,
        balance: null,
        error: null
    });

    const [showPassword, setShowPassword] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);

    const [notificationSettings, setNotificationSettings] = useState({
        email: '',
        emailEnabled: false,
        telegramEnabled: false
    });

    const handleWgGesuchtConnect = () => {
        // Here you would handle the actual authentication
        if (wgGesuchtCredentials.email && wgGesuchtCredentials.password) {
            setWgGesuchtCredentials(prev => ({
                ...prev,
                status: 'connected'
            }));
        }
    };

    const handleOpenAiConnect = () => {
        // Here you would validate the API key
        if (openAiKey.key) {
            setOpenAiKey(prev => ({
                ...prev,
                status: true,
                balance: '25.00' // This would come from the API
            }));
        }
    };

    return (
        <div className="space-y-6 p-6">
            <h2 className="text-2xl font-bold">Personal Settings</h2>

            {/* WG-Gesucht Authentication */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        WG-Gesucht Authentication
                        {wgGesuchtCredentials.status === 'connected' ? (
                            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                Connected
                            </Badge>
                        ) : (
                            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                                Not Connected
                            </Badge>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {wgGesuchtCredentials.status === 'disconnected' ? (
                        <>
                            <div className="space-y-3">
                                <div className="space-y-2">
                                    <label className="text-sm text-gray-600">Email</label>
                                    <Input
                                        type="email"
                                        placeholder="Enter your WG-Gesucht email"
                                        value={wgGesuchtCredentials.email}
                                        onChange={(e) => setWgGesuchtCredentials(prev => ({
                                            ...prev,
                                            email: e.target.value
                                        }))}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-gray-600">Password</label>
                                    <div className="relative">
                                        <Input
                                            type={showPassword ? "text" : "password"}
                                            placeholder="Enter your password"
                                            value={wgGesuchtCredentials.password}
                                            onChange={(e) => setWgGesuchtCredentials(prev => ({
                                                ...prev,
                                                password: e.target.value
                                            }))}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                                        >
                                            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <Button
                                className="w-full"
                                onClick={handleWgGesuchtConnect}
                                disabled={!wgGesuchtCredentials.email || !wgGesuchtCredentials.password}
                            >
                                Connect Account
                            </Button>
                        </>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <Key className="h-4 w-4 text-gray-500" />
                                <span className="text-sm text-gray-600">
                                    Connected as {wgGesuchtCredentials.email}
                                </span>
                            </div>
                            <Button
                                variant="outline"
                                className="w-full"
                                onClick={() => setWgGesuchtCredentials(prev => ({
                                    ...prev,
                                    status: 'disconnected',
                                    password: ''
                                }))}
                            >
                                Disconnect
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* OpenAI API Status */}
            <Card>
                <CardHeader>
                    <CardTitle>OpenAI API Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {!openAiKey.status ? (
                        <>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-600">API Key</label>
                                <div className="relative">
                                    <Input
                                        type={showApiKey ? "text" : "password"}
                                        placeholder="Enter your OpenAI API key"
                                        value={openAiKey.key}
                                        onChange={(e) => setOpenAiKey(prev => ({
                                            ...prev,
                                            key: e.target.value
                                        }))}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowApiKey(!showApiKey)}
                                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                                    >
                                        {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                    </button>
                                </div>
                            </div>
                            <Button
                                className="w-full"
                                onClick={handleOpenAiConnect}
                                disabled={!openAiKey.key}
                            >
                                Connect API
                            </Button>
                        </>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <CreditCard className="h-4 w-4 text-gray-500" />
                                <span className="text-sm text-gray-600">
                                    Available Credits: ${openAiKey.balance}
                                </span>
                            </div>
                            {openAiKey.balance && Number(openAiKey.balance) < 5 && (
                                <div className="flex items-center gap-2 text-sm text-yellow-600">
                                    <AlertCircle className="h-4 w-4" />
                                    Low balance warning: Less than $5.00 remaining
                                </div>
                            )}
                            <Button
                                variant="outline"
                                className="w-full"
                                onClick={() => setOpenAiKey(prev => ({
                                    ...prev,
                                    status: false,
                                    key: '',
                                    balance: null
                                }))}
                            >
                                Disconnect API
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Notifications Card remains the same */}
            <Card>
                <CardHeader>
                    <CardTitle>Notification Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Mail className="h-4 w-4 text-gray-500" />
                            <span className="text-sm">Email Notifications</span>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setNotificationSettings(prev => ({
                                ...prev,
                                emailEnabled: !prev.emailEnabled
                            }))}
                        >
                            {notificationSettings.emailEnabled ? (
                                <Check className="h-4 w-4 text-green-500" />
                            ) : (
                                'Enable'
                            )}
                        </Button>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Bot className="h-4 w-4 text-gray-500" />
                            <span className="text-sm">Telegram Notifications</span>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setNotificationSettings(prev => ({
                                ...prev,
                                telegramEnabled: !prev.telegramEnabled
                            }))}
                        >
                            {notificationSettings.telegramEnabled ? (
                                <Check className="h-4 w-4 text-green-500" />
                            ) : (
                                'Enable'
                            )}
                        </Button>
                    </div>

                    {(notificationSettings.emailEnabled || notificationSettings.telegramEnabled) && (
                        <div className="mt-4 text-sm text-gray-500">
                            <Bell className="h-4 w-4 inline mr-2" />
                            You'll be notified when new listings match your search criteria
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default ProfileView;