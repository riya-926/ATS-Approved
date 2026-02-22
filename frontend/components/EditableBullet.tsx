'use client';

import { useState, useRef, useEffect } from 'react';

interface EditableBulletProps {
  id: string;
  content: string;
  suggestedText: string;
  originalText: string;
  isRejected: boolean;
  editedText?: string;
  onReject: (id: string) => void;
  onEdit: (id: string, text: string) => void;
  onRemove?: (id: string) => void;
  onRedo?: (id: string) => void;
  isRedoing?: boolean;
  /** If true, show live "AI editing" animation (typing effect) */
  showLiveEdit?: boolean;
}

export default function EditableBullet({
  id,
  content,
  suggestedText,
  originalText,
  isRejected,
  editedText,
  onReject,
  onEdit,
  onRemove,
  onRedo,
  isRedoing = false,
  showLiveEdit = false,
}: EditableBulletProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(editedText ?? content);
  const [liveText, setLiveText] = useState(showLiveEdit ? originalText : suggestedText);
  const [liveDone, setLiveDone] = useState(!showLiveEdit);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isEditing]);

  // Live typing effect when suggestion loads
  useEffect(() => {
    if (!showLiveEdit || liveDone || isRejected) {
      setLiveText(suggestedText);
      setLiveDone(true);
      return;
    }
    setLiveText(originalText);
    const target = suggestedText;
    let i = 0;
    const step = Math.max(1, Math.floor(target.length / 25));
    const interval = setInterval(() => {
      i = Math.min(i + step, target.length);
      setLiveText(target.slice(0, i));
      if (i >= target.length) {
        setLiveDone(true);
        clearInterval(interval);
      }
    }, 30);
    return () => clearInterval(interval);
  }, [showLiveEdit, suggestedText, originalText, isRejected, liveDone]);

  const displayText = editedText ?? (isRejected ? originalText : showLiveEdit ? liveText : originalText);

  const hasSuggestion = suggestedText !== originalText;

  const handleSaveEdit = () => {
    onEdit(id, editValue);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="group/bullet py-2">
        <textarea
          ref={textareaRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={handleSaveEdit}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSaveEdit();
            }
          }}
          rows={3}
          className="w-full px-3 py-2 border-2 border-purple-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
        />
        <div className="flex gap-2 mt-2">
          <button
            onClick={handleSaveEdit}
            className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
          >
            Save
          </button>
          <button
            onClick={() => {
              setEditValue(displayText);
              setIsEditing(false);
            }}
            className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="group/bullet relative py-2 pl-6 pr-2 -ml-2 rounded-lg hover:bg-purple-50/80 transition-colors overflow-visible"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {isHovered && onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(id);
          }}
          className="absolute right-full top-2 mr-1 px-1.5 py-0.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded whitespace-nowrap"
          title="Remove bullet point"
        >
          Remove
        </button>
      )}
      <span className="absolute left-0 text-gray-400">•</span>
      <div
        className="cursor-text select-text min-h-[1.5em]"
        onClick={() => setIsEditing(true)}
      >
        {displayText}
        {!liveDone && showLiveEdit && !isRejected && (
          <span className="inline-block w-2 h-4 ml-0.5 bg-purple-500 animate-pulse" />
        )}
      </div>

      {hasSuggestion && isHovered && (
        <div className="absolute top-2 right-2 flex gap-1 bg-white shadow-lg border border-gray-200 rounded-lg p-1 z-10">
          {onRedo && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRedo(id);
              }}
              disabled={isRedoing}
              className="p-1.5 rounded hover:bg-blue-100 text-gray-600 disabled:opacity-50"
              title="Generate new AI version"
            >
              {isRedoing ? (
                <svg className="w-4 h-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              )}
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onReject(id);
            }}
            className={`p-1.5 rounded hover:bg-red-100 ${isRejected ? 'bg-red-100 text-red-700' : 'text-gray-600'}`}
            title="Revert to original"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setEditValue(displayText);
              setIsEditing(true);
            }}
            className="p-1.5 rounded hover:bg-purple-100 text-gray-600"
            title="Edit directly"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
