'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function DownloadPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadReady, setDownloadReady] = useState(false);

  useEffect(() => {
    // Check if we have the necessary data
    const finalDecisions = sessionStorage.getItem('finalDecisions');
    const resumeData = sessionStorage.getItem('resumeData');
    
    if (!finalDecisions || !resumeData) {
      router.push('/');
    }
  }, [router]);

  const handleDownload = async () => {
    setLoading(true);
    setError('');

    try {
      const finalDecisions = JSON.parse(sessionStorage.getItem('finalDecisions') || '[]');
      const resumeData = JSON.parse(sessionStorage.getItem('resumeData') || '{}');
      const resumeFileName = sessionStorage.getItem('resumeFileName') || 'resume.docx';

      // Call backend to apply edits and generate final DOCX
      const response = await axios.post(
        '/api/rewrite/apply',
        {
          resume_json: resumeData,
          decisions: finalDecisions,
          original_filename: resumeFileName,
        },
        {
          responseType: 'blob',
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tailored_${resumeFileName}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setDownloadReady(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate tailored resume');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-xl rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Download Your Tailored Resume
          </h1>

          {downloadReady ? (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Download Complete!
              </h2>
              <p className="text-gray-600 mb-6">
                Your tailored resume has been downloaded. Review it to ensure all changes are correct.
              </p>
              <button
                onClick={() => router.push('/')}
                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                Start Over
              </button>
            </div>
          ) : (
            <>
              <p className="text-gray-600 mb-6">
                Your resume has been optimized based on your review decisions. Click the button below to download your tailored resume.
              </p>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                  {error}
                </div>
              )}

              <button
                onClick={handleDownload}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-4 px-6 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
              >
                {loading ? 'Generating Resume...' : 'Download Tailored Resume'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
