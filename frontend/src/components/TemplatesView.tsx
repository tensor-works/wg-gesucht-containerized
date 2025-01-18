import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Plus, Trash2, CheckCircle, Edit3, List, XCircle, Send } from 'lucide-react';

interface Template {
    id: string;
    name: string;
    content: string;
    doList: string[];
    dontList: string[];
}

const TemplatesView: React.FC = () => {
    const [templates, setTemplates] = useState<Template[]>([
        {
            id: '1',
            name: 'Roommate Inquiry',
            content: 'Hi {name}, I saw your listing in {neighborhood} and I’m interested...',
            doList: ['Be polite', 'Use a formal tone'],
            dontList: ['Don’t ask about personal details'],
        },
    ]);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>('1');
    const [newTemplateName, setNewTemplateName] = useState('');
    const [editContent, setEditContent] = useState('');
    const [doItem, setDoItem] = useState('');
    const [dontItem, setDontItem] = useState('');
    const [chatMessages, setChatMessages] = useState<{ role: string; message: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [selectedGPTModel, setSelectedGPTModel] = useState('gpt-3.5-turbo');

    const selectedTemplate = templates.find((template) => template.id === selectedTemplateId);

    const handleAddTemplate = () => {
        const newTemplate: Template = {
            id: String(templates.length + 1),
            name: newTemplateName || `New Template ${templates.length + 1}`,
            content: '',
            doList: [],
            dontList: [],
        };
        setTemplates([...templates, newTemplate]);
        setNewTemplateName('');
        setSelectedTemplateId(newTemplate.id);
    };

    const handleDeleteTemplate = (id: string) => {
        setTemplates(templates.filter((template) => template.id !== id));
        if (id === selectedTemplateId) {
            setSelectedTemplateId(null);
        }
    };

    const handleAddDo = () => {
        if (doItem && selectedTemplate) {
            setTemplates(
                templates.map((template) =>
                    template.id === selectedTemplateId
                        ? { ...template, doList: [...template.doList, doItem] }
                        : template
                )
            );
            setDoItem('');
        }
    };

    const handleAddDont = () => {
        if (dontItem && selectedTemplate) {
            setTemplates(
                templates.map((template) =>
                    template.id === selectedTemplateId
                        ? { ...template, dontList: [...template.dontList, dontItem] }
                        : template
                )
            );
            setDontItem('');
        }
    };

    const handleCorrectTemplate = () => {
        alert('Request sent to LLM to correct the template content!');
    };

    const handleSendChatMessage = () => {
        if (chatInput.trim()) {
            setChatMessages([...chatMessages, { role: 'user', message: chatInput }]);
            setChatInput('');

            // Simulate bot response
            setTimeout(() => {
                setChatMessages((prevMessages) => [
                    ...prevMessages,
                    { role: 'bot', message: 'This is a simulated response from the bot.' },
                ]);
            }, 1000);
        }
    };

    return (
        <div className="flex h-full">
            {/* Vertical Navigation Pane */}
            <div className="w-1/4 p-4 border-r bg-gray-50">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">Templates</h3>
                    <Button variant="outline" size="sm" onClick={handleAddTemplate}>
                        <Plus className="h-4 w-4" />
                    </Button>
                </div>
                <div className="space-y-2">
                    {templates.map((template) => (
                        <div
                            key={template.id}
                            className={`p-2 rounded cursor-pointer ${template.id === selectedTemplateId ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
                                }`}
                            onClick={() => setSelectedTemplateId(template.id)}
                        >
                            {template.name}
                        </div>
                    ))}
                </div>
            </div>

            {/* Template Editor */}
            <div className="w-3/4 p-6 space-y-6">
                {selectedTemplate ? (
                    <>
                        {/* Template Name */}
                        <div className="flex items-center justify-between">
                            <Input
                                value={selectedTemplate.name}
                                onChange={(e) =>
                                    setTemplates(
                                        templates.map((template) =>
                                            template.id === selectedTemplateId
                                                ? { ...template, name: e.target.value }
                                                : template
                                        )
                                    )
                                }
                                placeholder="Template Name"
                                className="w-3/4"
                            />
                            <Button variant="outline" size="sm" onClick={() => handleDeleteTemplate(selectedTemplate.id)}>
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>

                        {/* Template Content */}
                        <Textarea
                            value={selectedTemplate.content}
                            onChange={(e) =>
                                setTemplates(
                                    templates.map((template) =>
                                        template.id === selectedTemplateId
                                            ? { ...template, content: e.target.value }
                                            : template
                                    )
                                )
                            }
                            placeholder="Write your template here..."
                            className="w-full h-40"
                        />

                        <Button variant="default" size="sm" onClick={handleCorrectTemplate}>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Correct Template
                        </Button>

                        {/* Do and Don't Lists */}
                        <div className="grid grid-cols-2 gap-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Do List</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        {selectedTemplate.doList.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-2">
                                                <List className="h-4 w-4 text-gray-500" />
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                        <div className="flex gap-2 mt-2">
                                            <Input
                                                value={doItem}
                                                onChange={(e) => setDoItem(e.target.value)}
                                                placeholder="Add an item..."
                                            />
                                            <Button size="sm" onClick={handleAddDo}>
                                                <Plus className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>Don't List</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        {selectedTemplate.dontList.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-2">
                                                <XCircle className="h-4 w-4 text-gray-500" />
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                        <div className="flex gap-2 mt-2">
                                            <Input
                                                value={dontItem}
                                                onChange={(e) => setDontItem(e.target.value)}
                                                placeholder="Add an item..."
                                            />
                                            <Button size="sm" onClick={handleAddDont}>
                                                <Plus className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Chat with Bot */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Chat with Bot</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {/* Select GPT Model */}
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-gray-700">Select GPT Model</label>
                                    <select
                                        value={selectedGPTModel}
                                        onChange={(e) => setSelectedGPTModel(e.target.value)}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200"
                                    >
                                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                        <option value="gpt-4">GPT-4</option>
                                    </select>
                                </div>

                                {/* Chat Messages */}
                                <div className="space-y-4 max-h-40 overflow-y-auto border p-3 rounded bg-gray-50">
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
                                <div className="flex items-center gap-2 mt-4">
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
                    <div className="text-center text-gray-500">Select a template to start editing</div>
                )}
            </div>
        </div>
    );
};

export default TemplatesView;
