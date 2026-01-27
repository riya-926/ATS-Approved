'use client';

import { useState } from 'react';
import DiffView from './DiffView';

interface Suggestion {
  content_unit_id: string;
  original_text: string;
  suggested_text: string;
  confidence: number;
  reasoning: string;
  jd_alignment: {
    skills_addressed?: string[];
    responsibilities_addressed?: string[];
    ats_keywords_added?: string[];
  };
  preserves_meaning: boolean;
  risk_score: number;
}

interface SuggestionCardProps {
  suggestion: Suggestion;
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
  onEdit: (id: string, editedText: string) => void;
}

export default function SuggestionCard({
  suggestion,
  onAccept,
  onReject,
  onEdit,
}: SuggestionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(suggestion.suggested_text);
  const [isAccepted, setIsAccepted] = useState(false);
  const [isRejected, setIsRejected] = useState(false);

  const keywords = [
    ...(suggestion.jd_alignment.skills_addressed || []),
    ...(suggestion.jd_alignment.ats_keywords_added || []),
  ];

  const handleAccept = () => {
    setIsAccepted(true);
    setIsRejected(false);
    onAccept(suggestion.content_unit_id);
  };

  const handleReject = () => {
    setIsRejected(true);
    setIsAccepted(false);
    onReject(suggestion.content_unit_id);
  };

  const handleEdit = () => {
    if (isEditing) {
      onEdit(suggestion.content_unit_id, editedText);
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  const handleSaveEdit = () => {
    onEdit(suggestion.content_unit_id, editedText);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedText(suggestion.suggested_text);
    setIsEditing(false);
  };

  // Risk warnings
  const riskWarnings: string[] = [];
  if (suggestion.risk_score > 0.7) {
    riskWarnings.push('High risk: This suggestion may violate constraints');
  }
  if (!suggestion.preserves_meaning) {
    riskWarnings.push('Warning: Meaning may not be preserved');
  }

  return (
    <div
      className={`border rounded-lg p-6 ${
        isAccepted
          ? 'bg-green-50 border-green-300'
          : isRejected
          ? 'bg-red-50 border-red-300'
          : 'bg-white border-gray-200'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {suggestion.content_unit_id}
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-600">
              Confidence: <span className="font-semibold">{Math.round(suggestion.confidence * 100)}%</span>
            </span>
            <span className="text-gray-600">
              Risk Score: <span className={`font-semibold ${suggestion.risk_score > 0.7 ? 'text-red-600' : suggestion.risk_score > 0.3 ? 'text-yellow-600' : 'text-green-600'}`}>
                {Math.round(suggestion.risk_score * 100)}%
              </span>
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {isAccepted && (
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Accepted
            </span>
          )}
          {isRejected && (
            <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
              Rejected
            </span>
          )}
        </div>
      </div>

      {/* Risk Warnings */}
      {riskWarnings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <h4 className="text-sm font-semibold text-yellow-800 mb-1">⚠️ Risk Warnings:</h4>
          <ul className="list-disc list-inside text-sm text-yellow-700">
            {riskWarnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* JD Alignment Info */}
      {keywords.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <h4 className="text-sm font-semibold text-blue-800 mb-1">Keywords Added:</h4>
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Reasoning */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-1">Reasoning:</h4>
        <p className="text-sm text-gray-600">{suggestion.reasoning}</p>
      </div>

      {/* Diff View or Edit Mode */}
      {isEditing ? (
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Edit Suggested Text:
          </label>
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSaveEdit}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Save
            </button>
            <button
              onClick={handleCancelEdit}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="mb-4">
          <DiffView
            original={suggestion.original_text}
            suggested={suggestion.suggested_text}
            keywords={keywords}
          />
        </div>
      )}

      {/* Action Buttons */}
      {!isAccepted && !isRejected && (
        <div className="flex gap-3">
          <button
            onClick={handleAccept}
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
          >
            ✓ Accept
          </button>
          <button
            onClick={handleEdit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            ✏️ Edit
          </button>
          <button
            onClick={handleReject}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
          >
            ✗ Reject
          </button>
        </div>
      )}

      {/* Status Actions */}
      {(isAccepted || isRejected) && (
        <div className="flex gap-3">
          <button
            onClick={() => {
              setIsAccepted(false);
              setIsRejected(false);
            }}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 font-medium"
          >
            Undo
          </button>
        </div>
      )}
    </div>
  );
}
