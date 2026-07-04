import React from 'react';
import { useNotifications } from './NotificationContext';
import NotificationItem from './NotificationItem';
import { Check, BellOff } from 'lucide-react';

const NotificationDropdown = ({ onClose }) => {
    const { notifications, unreadCount, markAllAsRead } = useNotifications();

    const handleViewAll = () => {
        // Dispatch custom event to tell App to change view
        window.dispatchEvent(new CustomEvent('navigate', { detail: { view: 'notifications' } }));
        if (onClose) onClose();
    };

    const displayNotifications = notifications.slice(0, 5); // Show only top 5

    return (
        <div className="bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[85vh]">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                <h3 className="font-semibold text-gray-800">Notifications</h3>
                {unreadCount > 0 && (
                    <button
                        onClick={markAllAsRead}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 px-2 py-1 rounded-md hover:bg-blue-50 transition-colors"
                    >
                        <Check size={14} />
                        Mark all read
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[400px]">
                {displayNotifications.length > 0 ? (
                    <div className="divide-y divide-gray-100">
                        {displayNotifications.map((notification) => (
                            <NotificationItem 
                                key={notification.id} 
                                notification={notification} 
                                isDropdown={true}
                                onClose={onClose}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                        <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-3">
                            <BellOff className="text-gray-400" size={24} />
                        </div>
                        <p className="text-gray-500 font-medium">You're all caught up!</p>
                        <p className="text-gray-400 text-sm mt-1">No new notifications</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
                <div className="border-t border-gray-100 p-2 bg-gray-50/50">
                    <button
                        onClick={handleViewAll}
                        className="w-full py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                        View all notifications
                    </button>
                </div>
            )}
        </div>
    );
};

export default NotificationDropdown;
