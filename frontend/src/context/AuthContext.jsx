/**
 * EduSync — Auth Context.
 * Provides login, logout, user state, and loading state.
 */
import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // On mount — check if we have a valid token
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            api.get('/auth/me/')
                .then(res => setUser(res.data.data))
                .catch(() => {
                    localStorage.clear();
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email, password) => {
        const { data } = await api.post('/auth/login/', { email, password });
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        const meResp = await api.get('/auth/me/');
        setUser(meResp.data.data);
        return meResp.data.data;
    };

    const logout = async () => {
        const refresh = localStorage.getItem('refresh_token');
        try {
            if (refresh) await api.post('/auth/logout/', { refresh });
        } catch {
            // Ignore logout errors
        }
        localStorage.clear();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be inside AuthProvider');
    return ctx;
}
