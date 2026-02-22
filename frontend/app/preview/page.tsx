'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';

interface ContentUnit {
  id: string;
  type: string;
  content: string;
}

interface ResumeData {
  content_units: ContentUnit[];
  display_order?: { kind: string; content?: string; display_type?: string; unit_id?: string }[];
}

interface Decision {
  content_unit_id: string;
  final_text: string;
  status?: string;
}

export default function PreviewPage() {
  const router = useRouter();
  const [resumeData, setResumeData] = useState<ResumeData | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [exportModal, setExportModal] = useState<'docx' | 'pdf' | null>(null);
  const [exportFileName, setExportFileName] = useState('');

  useEffect(() => {
    const finalDecisions = sessionStorage.getItem('finalDecisions');
    const resumeDataStr = sessionStorage.getItem('resumeData');
    const fname = sessionStorage.getItem('resumeFileName') || 'resume.docx';

    if (!finalDecisions || !resumeDataStr) {
      router.push('/upload');
      return;
    }

    try {
      setResumeData(JSON.parse(resumeDataStr));
      setDecisions(JSON.parse(finalDecisions));
      setFileName(fname);
    } catch {
      router.push('/upload');
    }
  }, [router]);

  const finalTextMap = new Map(decisions.map((d) => [d.content_unit_id, d.final_text]));
  const removedIds = new Set(decisions.filter((d) => d.status === 'removed').map((d) => d.content_unit_id));
  const unitMap = new Map((resumeData?.content_units || []).map((u) => [u.id, u]));

  const getDisplayText = (unitId: string) => finalTextMap.get(unitId) ?? unitMap.get(unitId)?.content ?? '';

  const openExportModal = (format: 'docx' | 'pdf') => {
    const baseName = (fileName || 'resume').replace(/\.docx$/i, '');
    setExportFileName(`tailored_${baseName}`);
    setExportModal(format);
  };

  const handleDownload = async (format: 'docx' | 'pdf', customName?: string) => {
    setLoading(format);
    setError('');

    try {
      const finalDecisions = JSON.parse(sessionStorage.getItem('finalDecisions') || '[]');
      const resumeDataObj = JSON.parse(sessionStorage.getItem('resumeData') || '{}');
      const resumeFileName = sessionStorage.getItem('resumeFileName') || 'resume.docx';

      const endpoint = format === 'pdf' ? '/api/rewrite/apply-pdf' : '/api/rewrite/apply';

      const response = await axios.post(
        endpoint,
        {
          resume_json: resumeDataObj,
          decisions: finalDecisions,
          original_filename: resumeFileName,
        },
        { responseType: 'blob' }
      );

      const ext = format === 'pdf' ? '.pdf' : '.docx';
      const base = (customName || resumeFileName).replace(/\.(docx|pdf)$/gi, '').trim() || 'resume';
      const downloadName = `${base}${ext}`;

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', downloadName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      let msg = 'Download failed.';
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        if (typeof data === 'string') msg = data;
        else if (data && typeof data === 'object' && 'detail' in data) msg = String((data as { detail?: unknown }).detail);
        else if (data instanceof Blob) {
          try {
            const text = await data.text();
            try {
              const json = JSON.parse(text) as { detail?: string };
              msg = json.detail ?? text;
            } catch {
              msg = text || 'Download failed. Try DOCX if PDF fails.';
            }
          } catch {
            msg = 'Download failed. Try DOCX if PDF fails.';
          }
        } else msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(null);
      setExportModal(null);
    }
  };

  const confirmExport = () => {
    if (exportModal) {
      handleDownload(exportModal, exportFileName || undefined);
    }
  };

  if (!resumeData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
      </div>
    );
  }

  const displayOrder = resumeData.display_order || [];
  const hasDisplayOrder = displayOrder.length > 0;

  const renderDisplayItem = (item: { kind: string; content?: string; display_type?: string; unit_id?: string }, i: number) => {
    if (item.kind === 'display' && item.content) {
      const dt = item.display_type || '';
      if (dt === 'name') return <h2 key={i} className="text-2xl font-bold text-gray-900 text-center mb-1">{item.content}</h2>;
      if (dt === 'contact') return <p key={i} className="text-gray-500 text-sm text-center mb-8">{item.content}</p>;
      if (dt === 'section_header') return <h3 key={i} className="text-lg font-semibold text-gray-900 mt-6 mb-3">{item.content}</h3>;
      if (dt === 'job_title') return <p key={i} className="font-semibold text-gray-900 mt-4 mb-0">{item.content}</p>;
      if (dt === 'company_dates') return <p key={i} className="text-gray-600 text-sm mb-2">{item.content}</p>;
      if (dt === 'education_degree') return <p key={i} className="font-semibold text-gray-900 mt-2 mb-0">{item.content}</p>;
      if (dt === 'education_school') return <p key={i} className="text-gray-600 text-sm mb-4">{item.content}</p>;
      return <p key={i} className="text-gray-700 mb-2">{item.content}</p>;
    }
    if (item.kind === 'editable' && item.unit_id) {
      if (removedIds.has(item.unit_id)) return null;
      const content = getDisplayText(item.unit_id);
      const unit = unitMap.get(item.unit_id);
      const isSkillsLine = unit?.type === 'skills_line';
      if (isSkillsLine) return <p key={i} className="text-gray-700 py-2 mb-4">{content}</p>;
      return (
        <p key={i} className="text-gray-700 py-1 pl-6 -ml-2 relative">
          <span className="absolute left-0 text-gray-400">•</span>
          {content}
        </p>
      );
    }
    return null;
  };

  // Fallback when no display_order
  const itemsToRender = hasDisplayOrder
    ? displayOrder
    : [
        { kind: 'display', content: 'John Doe', display_type: 'name' },
        { kind: 'display', content: 'john.doe@email.com • (555) 123-4567 • linkedin.com/in/johndoe', display_type: 'contact' },
        { kind: 'display', content: 'Professional Summary', display_type: 'section_header' },
        ...(resumeData.content_units || []).filter((u) => u.type === 'summary').map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Work Experience', display_type: 'section_header' },
        ...(resumeData.content_units || []).filter((u) => u.type === 'experience_bullet' || u.id.includes('exp_bullet')).map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Projects', display_type: 'section_header' },
        ...(resumeData.content_units || []).filter((u) => u.type === 'project_description' || u.id.includes('proj_bullet')).map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
        { kind: 'display', content: 'Skills', display_type: 'section_header' },
        ...(resumeData.content_units || []).filter((u) => u.type === 'skills_line' || u.id.includes('skills')).map((u) => ({ kind: 'editable' as const, unit_id: u.id })),
      ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/review"
            className="inline-flex items-center text-purple-600 hover:text-purple-700 font-medium"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Editing
          </Link>
          <div className="flex gap-3">
            <button
              onClick={() => openExportModal('docx')}
              disabled={!!loading}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading === 'docx' ? (
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )}
              Export DOCX
            </button>
            <button
              onClick={() => openExportModal('pdf')}
              disabled={!!loading}
              className="px-4 py-2 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading === 'pdf' ? (
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )}
              Export PDF
            </button>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Resume Preview</h1>
        <p className="text-gray-500 mb-6">{fileName}</p>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {exportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Export Resume as {exportModal === 'pdf' ? 'PDF' : 'DOCX'}
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">File Name</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={exportFileName}
                    onChange={(e) => setExportFileName(e.target.value)}
                    placeholder="Enter file name"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                  <span className="text-gray-500 text-sm">.{exportModal}</span>
                </div>
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setExportModal(null)}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmExport}
                  disabled={!!loading}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {loading === exportModal ? (
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  )}
                  Download
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 sm:p-12 max-w-3xl mx-auto">
          {itemsToRender.map((item, i) => renderDisplayItem(item, i))}
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/review"
            className="px-6 py-3 rounded-lg border-2 border-purple-600 text-purple-600 font-semibold hover:bg-purple-50 text-center"
          >
            Back to Editing
          </Link>
          <button
            onClick={() => openExportModal('docx')}
            disabled={!!loading}
            className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            Export as DOCX
          </button>
          <button
            onClick={() => openExportModal('pdf')}
            disabled={!!loading}
            className="px-6 py-3 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 disabled:opacity-50"
          >
            Export as PDF
          </button>
        </div>

        <div className="mt-8 text-center">
          <Link href="/upload" className="text-purple-600 hover:text-purple-700 font-medium text-sm">
            Start Over with a New Resume
          </Link>
        </div>
      </div>
    </div>
  );
}
