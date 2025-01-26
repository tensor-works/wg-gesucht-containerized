import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import {
    Key,
    Mail,
    Bell,
    CreditCard,
    Check,
    AlertCircle,
    Bot,
    Eye,
    EyeOff,
    Loader2
} from 'lucide-react';

const ProfileView = () => {
    // Existing state
    const [wgGesuchtCredentials, setWgGesuchtCredentials] = useState({
        email: '',
        password: '',
        status: 'disconnected' as 'connected' | 'disconnected',
    });

    const [openAiKey, setOpenAiKey] = useState<{
        key: string;
        status: boolean;
        balance: string | null;
        error: string | null;
    }>({
        key: '',
        status: false,
        balance: null,
        error: null,
    });

    const [showPassword, setShowPassword] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);

    const [notificationSettings, setNotificationSettings] = useState({
        email: '',
        emailEnabled: false,
        telegramEnabled: false,
    });

    // New state for API integration
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Fetch initial settings
    useEffect(() => {
        const fetchSettings = async () => {
            try {
                setLoading(true);
                // Fetch OpenAI balance if key exists
                if (openAiKey.status) {
                    const balanceResponse = await fetch('/api/v1/settings/openai-balance');
                    if (balanceResponse.ok) {
                        const balanceData = await balanceResponse.json();
                        setOpenAiKey(prev => ({
                            ...prev,
                            balance: balanceData.balance.toFixed(2)
                        }));
                    }
                }

                // Fetch profile photo (if needed)
                const photoResponse = await fetch('/api/v1/settings/profile-photo');
                if (!photoResponse.ok) {
                    console.warn('Failed to load profile photo');
                }
            } catch (err) {
                setError('Failed to load settings');
                console.error('Error loading settings:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchSettings();
    }, [openAiKey.status]);

    const handleWgGesuchtConnect = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch('/api/v1/settings/credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential_type: 'wg_gesucht',
                    wg_gesucht: {
                        email: wgGesuchtCredentials.email,
                        password: wgGesuchtCredentials.password
                    }
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to connect WG-Gesucht account');
            }

            setWgGesuchtCredentials(prev => ({
                ...prev,
                status: 'connected'
            }));

            setSuccess('WG-Gesucht account connected successfully');
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError('Failed to connect WG-Gesucht account');
            console.error('Error connecting account:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenAiConnect = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch('/api/v1/settings/credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential_type: 'openai',
                    openai: {
                        api_key: openAiKey.key,
                        user_id: 'current-user'
                    }
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to connect OpenAI API');
            }

            // Rest of your existing code...

        } catch (err) {
            setError('Failed to connect OpenAI API');
            console.error('Error connecting OpenAI:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 p-6">
            <h2 className="text-2xl font-bold">Personal Settings</h2>

            {/* Error/Success Alerts */}
            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {success && (
                <Alert>
                    <Check className="h-4 w-4" />
                    <AlertTitle>Success</AlertTitle>
                    <AlertDescription>{success}</AlertDescription>
                </Alert>
            )}

            {/* Rest of your existing JSX */}
            {/* WG-Gesucht Authentication Card */}
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
                    {/* Rest of WG-Gesucht card content */}
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
                                disabled={loading || !wgGesuchtCredentials.email || !wgGesuchtCredentials.password}
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Connecting...
                                    </>
                                ) : (
                                    'Connect Account'
                                )}
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
                                disabled={loading}
                            >
                                Disconnect
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* OpenAI API Card */}
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
                                disabled={loading || !openAiKey.key}
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Connecting...
                                    </>
                                ) : (
                                    'Connect API'
                                )}
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
                                disabled={loading}
                            >
                                Disconnect API
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Notifications Card */}
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
                            disabled={loading}
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
                            disabled={loading}
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