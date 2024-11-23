import React from 'react';

export interface FileUploadProps {
  onUpload: (file: File) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload }) => {
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="file-upload">
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileUpload}
        id="file-upload"
        style={{ display: 'none' }}
      />
      <label htmlFor="file-upload" className="upload-button">
        Upload PDF
      </label>
    </div>
  );
};

// Add this to make it a module
export {}; 