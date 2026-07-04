import React from 'react';
import { useNotifications } from './NotificationContext';
import { formatDistanceToNow } from 'date-fns';
import { 
    MessageSquare, 
    FileText, 
    Star, 
    Home, 
    Info, 
    ShieldAlert, 
    Circle,
    Trash2
} from 'lucide-react';

const NotificationItem = ({ notification, isDropdown = false, onClose }) => {
    const { markAsRead, deleteNotification } = useNotifications();

    const getIcon = (type) => {
        switch (type) {
            case 'message':
            case 'chat': return <MessageSquare size={isDropdown ? 18 : 20} className="text-blue-500" />;
            case 'application': return <FileText size={isDropdown ? 18 : 20} className="text-emerald-500" />;
            case 'review': return <Star size={isDropdown ? 18 : 20} className="text-amber-500" />;
            case 'listing': return <Home size={isDropdown ? 18 : 20} className="text-indigo-500" />;
            case 'security': return <ShieldAlert size={isDropdown ? 18 : 20} className="text-red-500" />;
            case 'system':
            default: return <Info size={isDropdown ? 18 : 20} className="text-gray-500" />;
        }
    };

    const getBgColor = (priority, isRead) => {
        if (isRead) return 'bg-white hover:bg-gray-50';
        if (priority === 'urgent' || priority === 'high') return 'bg-red-50 hover:bg-red-100';
        return 'bg-blue-50/50 hover:bg-blue-50';
    };

    const handleClick = () => {
        if (!notification.is_read) {
            markAsRead(notification.id);
        }

        // Deep linking based on payload
        const { payload, notification_type } = notification;
        if (payload) {
            let targetView = null;
            if (payload.conversation_id && (notification_type === 'chat' || notification_type === 'message')) {
                targetView = 'chat'; // in this app, you can just go to chat
            } else if (payload.application_id) {
                targetView = 'dashboard';
            } else if (payload.listing_id) {
                targetView = 'listings';
            }
            if (targetView) {
                window.dispatchEvent(new CustomEvent('navigate', { detail: { view: targetView } }));
            }
        }

        if (onClose) onClose();
    };

    const handleDelete = (e) => {
        e.stopPropagation();
        deleteNotification(notification.id);
    };

    return (
        <div 
            onClick={handleClick}
            className={`group relative flex items-start gap-3 p-4 cursor-pointer transition-colors duration-200 ${getBgColor(notification.priority, notification.is_read)} ${!isDropdown ? 'rounded-xl border border-gray-100 shadow-sm mb-2' : ''}`}
        >
            {/* Icon */}
            <div className="flex-shrink-0 mt-1 bg-white p-2 rounded-full shadow-sm border border-gray-100">
                {getIcon(notification.notification_type)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pr-6">
                <div className="flex justify-between items-start mb-1">
                    <h4 className={`text-sm font-semibold truncate pr-2 ${notification.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                        {notification.title}
                    </h4>
                    <span className="text-xs text-gray-400 flex-shrink-0 whitespace-nowrap">
                        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                    </span>
                </div>
                <p className={`text-sm line-clamp-2 ${notification.is_read ? 'text-gray-500' : 'text-gray-700 font-medium'}`}>
                    {notification.message}
                </p>
            </div>

            {/* Actions (visible on hover) */}
            <div className={`absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity ${!isDropdown ? 'bg-white/80 backdrop-blur-sm p-1 rounded-lg' : ''}`}>
                {!notification.is_read && (
                    <button 
                        onClick={(e) => { e.stopPropagation(); markAsRead(notification.id); }}
                        className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-full"
                        title="Mark as read"
                    >
                        <Circle size={14} className="fill-current" />
                    </button>
                )}
                <button 
                    onClick={handleDelete}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full"
                    title="Delete notification"
                >
                    <Trash2 size={16} />
                </button>
            </div>

            {/* Unread dot indicator (always visible if unread) */}
            {!notification.is_read && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full group-hover:opacity-0 transition-opacity"></div>
            )}
        </div>
    );
};

export default NotificationItem;
