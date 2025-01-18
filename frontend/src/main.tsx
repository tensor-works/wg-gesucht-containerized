import React from 'react';
import ReactDOM from 'react-dom/client';
import MainLayout from './MainLayout';
import { BrowserRouter } from 'react-router-dom';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <BrowserRouter>
            <MainLayout />
        </BrowserRouter>
    </React.StrictMode>
);
