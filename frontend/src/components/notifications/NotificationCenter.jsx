import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import NotificationItem from './NotificationItem';
import { Bell, CheckSquare, Trash2 } from 'lucide-react';

const NotificationCenter = () => {
    const { 
        notifications, 
        loading, 
        markAllAsRead,
        refresh 
    } = useNotifications();

    const [filter, setFilter] = useState('all'); // all, unread

    useEffect(() => {
        // Refresh notifications when opening center to ensure fresh data
        refresh();
    }, [refresh]);

    const filteredNotifications = notifications.filter(n => 
        filter === 'all' ? true : !n.is_read
    );

    if (loading && notifications.length === 0) {
        return (
            <div className="max-w-4xl mx-auto p-6 animate-pulse">
                <div className="h-8 w-48 bg-gray-200 rounded mb-6"></div>
                <div className="space-y-4">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="h-24 bg-gray-100 rounded-xl"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-4 sm:p-6 min-h-[80vh]">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                {/* Header */}
                <div className="px-6 py-5 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-50 p-2.5 rounded-xl">
                            <Bell className="text-blue-600" size={24} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">Notifications</h1>
                            <p className="text-sm text-gray-500">Manage your alerts and updates</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="flex bg-gray-100 p-1 rounded-lg">
                            <button
                                onClick={() => setFilter('all')}
                                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${filter === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                All
                            </button>
                            <button
                                onClick={() => setFilter('unread')}
                                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${filter === 'unread' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                Unread
                            </button>
                        </div>
                        <button
                            onClick={markAllAsRead}
                            title="Mark all as read"
                            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-transparent hover:border-blue-100"
                        >
                            <CheckSquare size={20} />
                        </button>
                    </div>
                </div>

                {/* List */}
                <div className="p-6 bg-gray-50/30">
                    {filteredNotifications.length > 0 ? (
                        <div className="space-y-3">
                            {filteredNotifications.map(notification => (
                                <NotificationItem 
                                    key={notification.id} 
                                    notification={notification} 
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                                <Bell className="text-gray-300" size={40} />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900">No notifications yet</h3>
                            <p className="text-gray-500 max-w-sm mt-1">
                                {filter === 'unread' 
                                    ? "You've read all your notifications!" 
                                    : "When you get new updates about applications or messages, they'll show up here."}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NotificationCenter;
