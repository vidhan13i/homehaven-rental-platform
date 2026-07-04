import React, { useState, useRef, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import NotificationDropdown from './NotificationDropdown';
import { Bell } from 'lucide-react';

const NotificationBell = () => {
    const { unreadCount, loading } = useNotifications();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleDropdown = () => {
        setIsOpen(!isOpen);
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button 
                onClick={toggleDropdown}
                className="relative p-2 text-gray-600 hover:text-blue-600 transition-colors rounded-full hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Notifications"
            >
                <Bell size={24} />
                
                {/* Badge */}
                {!loading && unreadCount > 0 && (
                    <span className="absolute top-1 right-1 flex items-center justify-center min-w-5 h-5 px-1.5 text-xs font-bold text-white bg-red-500 rounded-full border-2 border-white transform translate-x-1/4 -translate-y-1/4 shadow-sm animate-pulse">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown content */}
            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 z-50 origin-top-right">
                    <NotificationDropdown onClose={() => setIsOpen(false)} />
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
