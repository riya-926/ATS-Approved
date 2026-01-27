'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import SuggestionCard from '@/components/SuggestionCard';
import axios from 'axios';

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

export default function ReviewPage() {
  const router = useRouter();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [acceptedIds, setAcceptedIds] = useState<Set<string>>(new Set());
  const [rejectedIds, setRejectedIds] = useState<Set<string>>(new Set());
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    accepted: 0,
    rejected: 0,
    edited: 0,
  });

  useEffect(() => {
    // Load data from sessionStorage
    const suggestionsData = sessionStorage.getItem('suggestions');
    if (!suggestionsData) {
      router.push('/');
      return;
    }

    try {
      const data = JSON.parse(suggestionsData);
      console.log('Loaded suggestions data:', data); // Debug log
      const suggestionsList = data.suggestions || [];
      console.log('Suggestions list:', suggestionsList); // Debug log
      setSuggestions(suggestionsList);
      setStats({
        total: suggestionsList.length || data.total_suggestions || 0,
        accepted: 0,
        rejected: 0,
        edited: 0,
      });
      
      // If no suggestions, show helpful message
      if (suggestionsList.length === 0) {
        setError('No suggestions were generated. This might mean your resume already matches the job description well, or there were no content units found to optimize.');
      }
    } catch (err) {
      console.error('Error parsing suggestions:', err);
      setError('Failed to load suggestions: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [router]);

  const handleAccept = (id: string) => {
    setAcceptedIds((prev) => new Set(prev).add(id));
    setRejectedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    setStats((prev) => ({
      ...prev,
      accepted: acceptedIds.has(id) ? prev.accepted : prev.accepted + 1,
      rejected: rejectedIds.has(id) ? prev.rejected - 1 : prev.rejected,
    }));
  };

  const handleReject = (id: string) => {
    setRejectedIds((prev) => new Set(prev).add(id));
    setAcceptedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    setStats((prev) => ({
      ...prev,
      rejected: rejectedIds.has(id) ? prev.rejected : prev.rejected + 1,
      accepted: acceptedIds.has(id) ? prev.accepted - 1 : prev.accepted,
    }));
  };

  const handleEdit = (id: string, editedText: string) => {
    setEditedTexts((prev) => ({ ...prev, [id]: editedText }));
    if (!editedTexts[id]) {
      setStats((prev) => ({ ...prev, edited: prev.edited + 1 }));
    }
  };

  const handleContinue = async () => {
    // Prepare final suggestions
    const finalSuggestions = suggestions.map((sug) => {
      if (acceptedIds.has(sug.content_unit_id)) {
        return {
          ...sug,
          final_text: editedTexts[sug.content_unit_id] || sug.suggested_text,
          status: 'accepted',
        };
      }
      return {
        ...sug,
        final_text: sug.original_text,
        status: rejectedIds.has(sug.content_unit_id) ? 'rejected' : 'pending',
      };
    });

    // Store final decisions
    sessionStorage.setItem('finalDecisions', JSON.stringify(finalSuggestions));
    router.push('/download');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading suggestions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Review Suggestions
          </h1>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-sm text-gray-600">Total</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.accepted}</div>
              <div className="text-sm text-gray-600">Accepted</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
              <div className="text-sm text-gray-600">Rejected</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.edited}</div>
              <div className="text-sm text-gray-600">Edited</div>
            </div>
          </div>
        </div>

        {/* Suggestions List */}
        {suggestions.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">
              No Suggestions Generated
            </h3>
            <p className="text-yellow-700 mb-4">
              This could mean:
            </p>
            <ul className="list-disc list-inside text-yellow-700 space-y-1 mb-4">
              <li>Your resume already matches the job description well</li>
              <li>No content units were found to optimize</li>
              <li>The resume format may not be compatible</li>
            </ul>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 font-medium"
            >
              Try Again with Different Resume
            </button>
          </div>
        ) : (
          <div className="space-y-6 mb-8">
            {suggestions.map((suggestion) => (
              <SuggestionCard
                key={suggestion.content_unit_id}
                suggestion={suggestion}
                onAccept={handleAccept}
                onReject={handleReject}
                onEdit={handleEdit}
              />
            ))}
          </div>
        )}

        {/* Continue Button */}
        <div className="bg-white shadow-lg rounded-lg p-6">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-600">
                Review all suggestions before continuing. You can always go back and change your decisions.
              </p>
            </div>
            <button
              onClick={handleContinue}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium text-lg"
            >
              Continue to Download →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
