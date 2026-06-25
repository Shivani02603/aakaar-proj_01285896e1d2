import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: string;
  username: string;
  email: string;
}

export const register = (data: RegisterRequest) =>
  api.post<RegisterResponse>('/api/auth/register', data);

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
}

export const login = (data: LoginRequest) =>
  api.post<LoginResponse>('/api/auth/login', data);

export interface UploadDocumentRequest {
  file: File;
}

export interface UploadDocumentResponse {
  id: string;
  name: string;
  status: string;
}

export const uploadDocument = (data: FormData) =>
  api.post<UploadDocumentResponse>('/api/documents/upload', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export interface ListDocumentsResponse {
  documents: {
    id: string;
    name: string;
    status: string;
  }[];
}

export const listDocuments = () =>
  api.get<ListDocumentsResponse>('/api/documents');

export interface IngestDocumentsRequest {
  documentIds: string[];
}

export interface IngestDocumentsResponse {
  success: boolean;
}

export const ingestDocuments = (data: IngestDocumentsRequest) =>
  api.post<IngestDocumentsResponse>('/api/ai/ingest', data);

export interface AIQueryRequest {
  query: string;
  sessionId: string;
}

export interface AIQueryResponse {
  answer: string;
  citations: {
    documentId: string;
    text: string;
  }[];
}

export const aiQuery = (data: AIQueryRequest) =>
  api.post<AIQueryResponse>('/api/ai/query', data);

export interface CreateChatSessionRequest {
  name: string;
}

export interface CreateChatSessionResponse {
  id: string;
  name: string;
}

export const createChatSession = (data: CreateChatSessionRequest) =>
  api.post<CreateChatSessionResponse>('/api/chat/sessions', data);

export interface ListChatSessionsResponse {
  sessions: {
    id: string;
    name: string;
  }[];
}

export const listChatSessions = () =>
  api.get<ListChatSessionsResponse>('/api/chat/sessions');

export interface GetChatMessagesResponse {
  messages: {
    id: string;
    sender: string;
    content: string;
    timestamp: string;
  }[];
}

export const getChatMessages = (sessionId: string) =>
  api.get<GetChatMessagesResponse>(`/api/chat/sessions/${sessionId}/messages`);

export interface StreamAnswerRequest {
  query: string;
  sessionId: string;
}

export const streamAnswer = (data: StreamAnswerRequest) =>
  api.post('/api/stream/answer', data, {
    responseType: 'stream',
  });