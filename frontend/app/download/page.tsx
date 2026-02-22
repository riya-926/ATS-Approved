'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';

export default function DownloadPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const finalDecisions = sessionStorage.getItem('finalDecisions');
    const resumeData = sessionStorage.getItem('resumeData');

    if (!finalDecisions || !resumeData) {
      router.push('/upload');
    }
  }, [router]);

  const handleDownload = async (format: 'docx' | 'pdf') => {
    setLoading(format);
    setError('');

    try {
      const finalDecisions = JSON.parse(sessionStorage.getItem('finalDecisions') || '[]');
      const resumeData = JSON.parse(sessionStorage.getItem('resumeData') || '{}');
      const resumeFileName = sessionStorage.getItem('resumeFileName') || 'resume.docx';

      const endpoint = format === 'pdf' ? '/api/rewrite/apply-pdf' : '/api/rewrite/apply';

      const response = await axios.post(endpoint, {
        resume_json: resumeData,
        decisions: finalDecisions,
        original_filename: resumeFileName,
      }, {
        responseType: 'blob',
      });

      const ext = format === 'pdf' ? '.pdf' : '.docx';
      const baseName = resumeFileName.replace(/\.docx$/i, '');
      const downloadName = `tailored_${baseName}${ext}`;

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
            msg = await data.text();
          } catch {
            msg = 'Download failed. Try DOCX if PDF fails.';
          }
        } else msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <Link
          href="/review"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Review
        </Link>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Export Your Optimized Resume
          </h1>
          <p className="text-gray-600 mb-8">
            Download your tailored resume in the format you need. DOCX is editable; PDF is best for ATS submission.
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid sm:grid-cols-2 gap-4">
            <button
              onClick={() => handleDownload('docx')}
              disabled={!!loading}
              className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-purple-400 hover:bg-purple-50/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                <svg className="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="font-semibold text-gray-900">Download DOCX</span>
              <span className="text-sm text-gray-500 text-center">Editable Word document</span>
              {loading === 'docx' && (
                <div className="animate-spin w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full" />
              )}
            </button>

            <button
              onClick={() => handleDownload('pdf')}
              disabled={!!loading}
              className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-purple-400 hover:bg-purple-50/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center group-hover:bg-red-200 transition-colors">
                <svg className="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <span className="font-semibold text-gray-900">Download PDF</span>
              <span className="text-sm text-gray-500 text-center">ATS-safe, ready to submit</span>
              {loading === 'pdf' && (
                <div className="animate-spin w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full" />
              )}
            </button>
          </div>

          <p className="mt-6 text-xs text-gray-500 text-center">
            PDF export requires Microsoft Word on Windows, or docx2pdf-compatible setup. If PDF fails, use DOCX and convert manually.
          </p>
        </div>

        <div className="mt-8 text-center">
          <Link
            href="/upload"
            className="text-purple-600 hover:text-purple-700 font-medium"
          >
            Start Over with a New Resume
          </Link>
        </div>
      </div>
    </div>
  );
}
