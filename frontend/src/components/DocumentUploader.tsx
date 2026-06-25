import React, { useState } from 'react';
import { ingestFile } from '../lib/aiApi';
import toast from 'react-hot-toast';

interface DocumentUploaderProps {
  sessionId: string;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setUploadProgress(0);
    setIsUploading(true);
    setSuccessMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token is missing.');
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${import.meta.env.VITE_API_BASE_URL}/api/documents/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('Accept', 'application/json');

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };

      xhr.onload = () => {
        setIsUploading(false);
        if (xhr.status >= 200 && xhr.status < 300) {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const response = JSON.parse(xhr.responseText);
            setSuccessMessage(`✓ Indexed ${response.chunks_indexed} chunks`);
          } else {
            throw new Error('Unexpected response format.');
          }
        } else {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const errorResponse = JSON.parse(xhr.responseText);
            throw new Error(errorResponse.message || 'Upload failed.');
          } else {
            throw new Error('Upload failed with an unknown error.');
          }
        }
      };

      xhr.onerror = () => {
        setIsUploading(false);
        throw new Error('Network error occurred during file upload.');
      };

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      xhr.send(formData);
    } catch (error: any) {
      setIsUploading(false);
      toast.error(error.message || 'An error occurred during file upload.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
      <div
        className="w-full h-32 flex items-center justify-center text-gray-500 cursor-pointer"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        Drag and drop a file here, or click to select
      </div>
      <input
        type="file"
        accept=".xlsx,.xls,.pdf,.docx"
        className="hidden"
        id="fileInput"
        onChange={handleFileSelect}
      />
      <label
        htmlFor="fileInput"
        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded cursor-pointer hover:bg-blue-600"
      >
        Select File
      </label>
      {isUploading && (
        <div className="w-full mt-4">
          <div className="relative w-full h-4 bg-gray-200 rounded">
            <div
              className="absolute top-0 left-0 h-4 bg-blue-500 rounded"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500 mt-1">{uploadProgress}%</p>
        </div>
      )}
      {successMessage && (
        <div className="mt-4 px-4 py-2 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;