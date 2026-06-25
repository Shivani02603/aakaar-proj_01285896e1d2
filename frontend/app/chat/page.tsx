'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatWindow from '@/components/ChatWindow';
import SessionSidebar from '@/components/SessionSidebar';
import DocumentUploader from '@/components/DocumentUploader';

export default function ChatPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>(undefined);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="flex items-center justify-between bg-blue-600 text-white px-4 py-2">
        <h1 className="text-lg font-bold">Aakaar Project</h1>
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 rounded"
        >
          Logout
        </button>
      </div>
      <div className="flex flex-1">
        <div className="w-64 bg-gray-100 border-r border-gray-300 flex flex-col">
          <SessionSidebar
            onSelectSession={handleSelectSession}
            activeSessionId={activeSessionId}
          />
          <DocumentUploader />
        </div>
        <div className="flex-1">
          <ChatWindow activeSessionId={activeSessionId} />
        </div>
      </div>
    </div>
  );
}