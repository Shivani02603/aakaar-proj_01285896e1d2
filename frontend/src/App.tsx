import { useState } from 'react';
import ChatWindow from '@/components/ChatWindow';
import DocumentUploader from '@/components/DocumentUploader';
import SessionSidebar from '@/components/SessionSidebar';

const App = () => {
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>(undefined);

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center justify-between px-6 py-4 bg-gray-800 text-white">
        <h1 className="text-lg font-bold">Aakaar Project</h1>
        <button
          onClick={() => setActiveSessionId(undefined)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium"
        >
          New Chat
        </button>
      </header>
      <div className="flex flex-1">
        <aside className="w-64 bg-gray-100 border-r border-gray-300">
          <SessionSidebar
            onSelectSession={handleSelectSession}
            activeSessionId={activeSessionId}
          />
          <div className="p-4 border-t border-gray-300">
            <DocumentUploader sessionId={activeSessionId} />
          </div>
        </aside>
        <main className="flex-1">
          <ChatWindow activeSessionId={activeSessionId} />
        </main>
      </div>
    </div>
  );
};

export default App;