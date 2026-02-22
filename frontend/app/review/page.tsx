'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import EditableBullet from '@/components/EditableBullet';
import axios from 'axios';

interface ContentUnit {
  id: string;
  type: string;
  content: string;
}

interface DisplayItem {
  kind: string;
  content?: string;
  display_type?: string;
  unit_id?: string;
}

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
  const [resumeData, setResumeData] = useState<{
    content_units: ContentUnit[];
    display_order?: DisplayItem[];
  } | null>(null);
  const [fileName, setFileName] = useState('');
  const [rejectedIds, setRejectedIds] = useState<Set<string>>(new Set());
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});
  const [redoingId, setRedoingId] = useState<string | null>(null);
  const [visibleIndex, setVisibleIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const jdSignals = typeof window !== 'undefined' ? sessionStorage.getItem('jdSignals') : null;
  const evidenceMap = typeof window !== 'undefined' ? sessionStorage.getItem('evidenceMap') : null;

  useEffect(() => {
    const suggestionsData = sessionStorage.getItem('suggestions');
    const resumeDataStr = sessionStorage.getItem('resumeData');
    const fname = sessionStorage.getItem('resumeFileName') || 'resume.docx';

    if (!suggestionsData || !resumeDataStr) {
      router.push('/upload');
      return;
    }

    try {
      const data = JSON.parse(suggestionsData);
      const suggestionsList = data.suggestions || [];
      setSuggestions(suggestionsList);
      setResumeData(JSON.parse(resumeDataStr));
      setFileName(fname);
      setVisibleIndex(0);

      if (suggestionsList.length === 0) {
        setError('No suggestions were generated. Your resume may already match the job description well.');
      }
    } catch (err) {
      setError('Failed to load suggestions.');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!loading && suggestions.length > 0) {
      const timers: ReturnType<typeof setTimeout>[] = [];
      suggestions.forEach((_, i) => {
        timers.push(setTimeout(() => setVisibleIndex((v) => Math.max(v, i + 1)), 200 + i * 150));
      });
      return () => timers.forEach(clearTimeout);
    }
  }, [loading, suggestions.length]);

  const suggestionMap = new Map(suggestions.map((s) => [s.content_unit_id, s]));
  const suggestionIdToIndex = new Map(suggestions.map((s, i) => [s.content_unit_id, i]));
  const unitMap = new Map((resumeData?.content_units || []).map((u) => [u.id, u]));

  const handleReject = (id: string) => {
    setRejectedIds((prev) => new Set(prev).add(id));
  };

  const handleRemove = (id: string) => {
    setRemovedIds((prev) => new Set(prev).add(id));
  };

  const handleEdit = (id: string, text: string) => {
    setEditedTexts((prev) => ({ ...prev, [id]: text }));
  };

  const handleRedo = async (id: string) => {
    if (!jdSignals || !evidenceMap || !resumeData) return;
    setRedoingId(id);
    try {
      const res = await axios.post('/api/rewrite/suggest-one', {
        content_unit_id: id,
        jd_signals: JSON.parse(jdSignals),
        evidence_map: JSON.parse(evidenceMap),
        resume_json: resumeData,
      });
      setSuggestions((prev) => prev.map((s) => (s.content_unit_id === id ? { ...s, ...res.data } : s)));
      setRejectedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      setEditedTexts((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch {
      // ignore
    } finally {
      setRedoingId(null);
    }
  };

  const handleContinue = () => {
    const editableUnitIds = new Set(
      (resumeData?.content_units || [])
        .filter((u) => u.type === 'experience_bullet' || u.type === 'project_description')
        .map((u) => u.id)
    );
    const finalSuggestions: Array<{
      content_unit_id: string;
      final_text: string;
      status: string;
      original_text?: string;
      suggested_text?: string;
    }> = [];

    for (const unitId of editableUnitIds) {
      if (removedIds.has(unitId)) {
        finalSuggestions.push({
          content_unit_id: unitId,
          final_text: '',
          status: 'removed',
          original_text: unitMap.get(unitId)?.content ?? '',
        });
        continue;
      }
      const sug = suggestionMap.get(unitId);
      if (rejectedIds.has(unitId)) {
        finalSuggestions.push({
          content_unit_id: unitId,
          final_text: sug?.original_text ?? unitMap.get(unitId)?.content ?? '',
          status: 'rejected',
          original_text: sug?.original_text,
          suggested_text: sug?.suggested_text,
        });
        continue;
      }
      const edited = editedTexts[unitId];
      const unit = unitMap.get(unitId);
      const finalText = edited ?? sug?.suggested_text ?? unit?.content ?? '';
      finalSuggestions.push({
        content_unit_id: unitId,
        final_text: finalText,
        status: 'accepted',
        original_text: sug?.original_text ?? unit?.content,
        suggested_text: sug?.suggested_text,
      });
    }
    sessionStorage.setItem('finalDecisions', JSON.stringify(finalSuggestions));
    router.push('/preview');
  };

  const getContentForUnit = (unitId: string) => {
    if (removedIds.has(unitId)) return '';
    const unit = unitMap.get(unitId);
    const sug = suggestionMap.get(unitId);
    if (!unit || !sug) return unit?.content ?? '';
    if (rejectedIds.has(unitId)) return sug.original_text;
    if (editedTexts[unitId]) return editedTexts[unitId];
    return sug.suggested_text;
  };

  const renderDisplayItem = (item: DisplayItem, index: number) => {
    if (item.kind === 'display' && item.content) {
      const dt = item.display_type || '';
      if (dt === 'name') {
        return (
          <h2 key={index} className="text-2xl font-bold text-gray-900 text-center mb-1">
            {item.content}
          </h2>
        );
      }
      if (dt === 'contact') {
        return (
          <p key={index} className="text-gray-500 text-sm text-center mb-8">
            {item.content}
          </p>
        );
      }
      if (dt === 'section_header') {
        return (
          <h3 key={index} className="text-lg font-semibold text-gray-900 mt-6 mb-3">
            {item.content}
          </h3>
        );
      }
      if (dt === 'job_title') {
        return (
          <p key={index} className="font-semibold text-gray-900 mt-4 mb-0">
            {item.content}
          </p>
        );
      }
      if (dt === 'company_dates') {
        return (
          <p key={index} className="text-gray-600 text-sm mb-2">
            {item.content}
          </p>
        );
      }
      if (dt === 'education_degree') {
        return (
          <p key={index} className="font-semibold text-gray-900 mt-2 mb-0">
            {item.content}
          </p>
        );
      }
      if (dt === 'education_school') {
        return (
          <p key={index} className="text-gray-600 text-sm mb-4">
            {item.content}
          </p>
        );
      }
      return <p key={index} className="text-gray-700 mb-2">{item.content}</p>;
    }

    if (item.kind === 'editable' && item.unit_id) {
      const unit = unitMap.get(item.unit_id);
      const sug = suggestionMap.get(item.unit_id) ?? (unit && (unit.type === 'experience_bullet' || unit.type === 'project_description')
        ? { content_unit_id: unit.id, original_text: unit.content, suggested_text: unit.content }
        : null);
      const sugIndex = suggestionIdToIndex.get(item.unit_id) ?? -1;
      const showLiveEdit = sug && sugIndex < visibleIndex;

      // Editable: Experience and Project bullets only. NOT Education, Skills/Additional.
      const isEditable = unit?.type === 'experience_bullet' || unit?.type === 'project_description';

      if (sug && isEditable) {
        if (removedIds.has(item.unit_id)) {
          return (
            <div key={item.unit_id} className="group/bullet relative py-2 pl-6 -ml-2 text-gray-400 line-through opacity-60">
              <span className="absolute left-0 text-gray-300">•</span>
              {sug.original_text}
            </div>
          );
        }
        return (
          <EditableBullet
            key={item.unit_id}
            id={item.unit_id}
            content={getContentForUnit(item.unit_id)}
            suggestedText={sug.suggested_text}
            originalText={sug.original_text}
            isRejected={rejectedIds.has(item.unit_id)}
            editedText={editedTexts[item.unit_id]}
            onReject={handleReject}
            onEdit={handleEdit}
            onRemove={handleRemove}
            onRedo={handleRedo}
            isRedoing={redoingId === item.unit_id}
            showLiveEdit={showLiveEdit}
          />
        );
      }

      // Display only (skills, education, or non-editable)
      const displayUnit = unitMap.get(item.unit_id);
      const displayContent = getContentForUnit(item.unit_id) || displayUnit?.content || '';
      const isSkillsLine = displayUnit?.type === 'skills_line';
      if (isSkillsLine) {
        return (
          <p key={item.unit_id} className="text-gray-700 py-2 mb-4">
            {displayContent}
          </p>
        );
      }
      return (
        <p key={item.unit_id} className="text-gray-700 py-1 pl-6 -ml-2 relative">
          <span className="absolute left-0 text-gray-400">•</span>
          {displayContent}
        </p>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading suggestions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg max-w-md">
          {error}
          <button
            onClick={() => router.push('/upload')}
            className="mt-4 block w-full py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const displayOrder = resumeData?.display_order || [];
  const hasDisplayOrder = displayOrder.length > 0;

  // Fallback: build display order from content_units if parser didn't return it
  const itemsToRender = hasDisplayOrder
    ? displayOrder
    : [
        { kind: 'display', content: 'John Doe', display_type: 'name' },
        { kind: 'display', content: 'john.doe@email.com • (555) 123-4567 • linkedin.com/in/johndoe', display_type: 'contact' },
        { kind: 'display', content: 'Professional Summary', display_type: 'section_header' },
        ...(resumeData?.content_units || [])
          .filter((u) => u.type === 'summary')
          .map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Work Experience', display_type: 'section_header' },
        ...(resumeData?.content_units || [])
          .filter((u) => u.type === 'experience_bullet' || u.id.includes('exp_bullet'))
          .map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Projects', display_type: 'section_header' },
        ...(resumeData?.content_units || [])
          .filter((u) => u.type === 'project_description' || u.id.includes('proj_bullet'))
          .map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Skills', display_type: 'section_header' },
        ...(resumeData?.content_units || [])
          .filter((u) => u.type === 'skills_line' || u.id.includes('skills'))
          .map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
      ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Resume Optimization</h1>
            <p className="text-gray-500 mt-1">{fileName}</p>
          </div>
          <button
            onClick={handleContinue}
            className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all shadow-md flex items-center gap-2"
          >
            Continue to Preview
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </button>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
          <p className="font-semibold text-purple-800 flex items-center gap-2 mb-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Your resume has been optimized!
          </p>
          <ul className="text-sm text-purple-700 space-y-1 list-disc list-inside">
            <li>Hover over Experience & Project bullets to see edit controls</li>
            <li>Remove — Remove bullet point (on left when hovering)</li>
            <li>Redo (🔄) — Generate new AI version</li>
            <li>X — Revert to original</li>
            <li>Click text to edit directly (Education & Skills are read-only)</li>
          </ul>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 sm:p-12 max-w-3xl mx-auto">
          {itemsToRender.map((item, i) => renderDisplayItem(item, i))}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={handleContinue}
            className="px-8 py-4 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold text-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg"
          >
            Continue to Preview →
          </button>
        </div>
      </div>
    </div>
  );
}
