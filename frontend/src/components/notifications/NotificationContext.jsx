import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../../api';

const NotificationContext = createContext(null);

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [socket, setSocket] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchNotifications = useCallback(async () => {
        try {
            // Wait for Nginx routing to be configured (Phase 6)
            const response = await api.get('/notifications/list/');
            setNotifications(response.data.results || []);
            
            const countRes = await api.get('/notifications/list/unread_count/');
            setUnreadCount(countRes.data.unread_count || 0);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchNotifications();
    }, [fetchNotifications]);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Ensure this matches the notification service port or gateway once configured
        const wsUrl = `ws://localhost:8000/ws/notifications/?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Connected to notification websocket');
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'notification') {
                const newNotification = message.data;
                setNotifications(prev => [newNotification, ...prev]);
                setUnreadCount(prev => prev + 1);
                
                // Native browser notification if granted
                if (Notification.permission === 'granted') {
                    new Notification(newNotification.title, {
                        body: newNotification.message
                    });
                }
            }
        };

        ws.onclose = () => {
            console.log('Disconnected from notification websocket');
        };

        setSocket(ws);

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, []);

    const markAsRead = async (id) => {
        try {
            await api.post(`/notifications/list/${id}/mark_read/`);
            setNotifications(prev => prev.map(n => 
                n.id === id ? { ...n, is_read: true } : n
            ));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            await api.post('/notifications/list/mark_all_read/');
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    };

    const deleteNotification = async (id) => {
        try {
            await api.delete(`/notifications/list/${id}/`);
            setNotifications(prev => {
                const target = prev.find(n => n.id === id);
                if (target && !target.is_read) {
                    setUnreadCount(count => Math.max(0, count - 1));
                }
                return prev.filter(n => n.id !== id);
            });
        } catch (error) {
            console.error('Failed to delete notification:', error);
        }
    };

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            loading,
            markAsRead,
            markAllAsRead,
            deleteNotification,
            refresh: fetchNotifications
        }}>
            {children}
        </NotificationContext.Provider>
    );
};
