'use client';

import { useEffect, useState } from 'react';

// Import diff-match-patch correctly for Next.js
// The library exports diff_match_patch (with underscores) as the constructor
const getDiffMatchPatch = () => {
  if (typeof window === 'undefined') return null;
  
  try {
    const dmp = require('diff-match-patch');
    // The library exports diff_match_patch as the constructor
    return dmp.diff_match_patch || dmp.DiffMatchPatch || dmp.default?.diff_match_patch || dmp.default;
  } catch (e) {
    console.error('Failed to load diff-match-patch:', e);
    return null;
  }
};

interface DiffViewProps {
  original: string;
  suggested: string;
  keywords?: string[];
}

export default function DiffView({ original, suggested, keywords = [] }: DiffViewProps) {
  const [diffs, setDiffs] = useState<Array<[number, string]>>([]);
  const [highlightedSuggested, setHighlightedSuggested] = useState<string>('');

  useEffect(() => {
    const DiffMatchPatchClass = getDiffMatchPatch();
    
    if (!DiffMatchPatchClass) {
      // Fallback: show simple comparison if diff library not available
      setDiffs([[0, original], [1, suggested]]);
      return;
    }
    
    try {
      const dmp = new DiffMatchPatchClass();
      const diff = dmp.diff_main(original, suggested);
      dmp.diff_cleanupSemantic(diff);
      setDiffs(diff);
    } catch (error) {
      console.error('Error computing diff:', error);
      // Fallback: show simple comparison
      setDiffs([[0, original], [1, suggested]]);
    }

    // Highlight keywords in suggested text
    let highlighted = suggested;
    keywords.forEach((keyword) => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlighted = highlighted.replace(
        regex,
        '<span class="keyword-highlight">$1</span>'
      );
    });
    setHighlightedSuggested(highlighted);
  }, [original, suggested, keywords]);

  return (
    <div className="space-y-4">
      {/* Original Text */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Original:</h4>
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <div className="text-gray-800 whitespace-pre-wrap">
            {diffs.map(([op, text], idx) => {
              if (op === -1) {
                return (
                  <span key={idx} className="diff-removed">
                    {text}
                  </span>
                );
              }
              return <span key={idx}>{text}</span>;
            })}
          </div>
        </div>
      </div>

      {/* Suggested Text */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Suggested:</h4>
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div
            className="text-gray-800 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: highlightedSuggested }}
          />
        </div>
      </div>

      {/* Diff Summary */}
      <div className="text-xs text-gray-500">
        {diffs.filter(([op]) => op !== 0).length > 0 && (
          <span>
            Changes: {diffs.filter(([op]) => op === 1).length} additions,{' '}
            {diffs.filter(([op]) => op === -1).length} deletions
          </span>
        )}
      </div>
    </div>
  );
}
