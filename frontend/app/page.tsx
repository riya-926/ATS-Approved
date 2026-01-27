'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function Home() {
  const router = useRouter();
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!resumeFile) {
      setError('Please upload a resume file');
      return;
    }

    if (!jdText.trim()) {
      setError('Please paste the job description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Step 1: Parse resume
      const formData = new FormData();
      formData.append('file', resumeFile);

      const parseResponse = await axios.post('/api/parse/docx', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Step 2: Extract JD signals
      const jdResponse = await axios.post('/api/jd/extract', {
        text: jdText,
      });

      // Step 3: Map evidence
      const evidenceResponse = await axios.post('/api/evidence/map', {
        jd_signals: jdResponse.data,
        resume_json: parseResponse.data,
      });

      // Step 4: Generate rewrite suggestions
      const rewriteResponse = await axios.post('/api/rewrite/suggest', {
        jd_signals: jdResponse.data,
        evidence_map: evidenceResponse.data,
        resume_json: parseResponse.data,
        max_suggestions: 10,
      });

      // Debug: Log response
      console.log('Rewrite response:', rewriteResponse.data);
      console.log('Suggestions count:', rewriteResponse.data.suggestions?.length || 0);

      // Check if we have content units
      if (!parseResponse.data.content_units || parseResponse.data.content_units.length === 0) {
        setError('No content units found in resume. Please ensure your resume has Experience, Skills, or Summary sections.');
        setLoading(false);
        return;
      }

      // Check if suggestions were generated
      if (!rewriteResponse.data.suggestions || rewriteResponse.data.suggestions.length === 0) {
        setError('No suggestions were generated. Your resume may already be well-optimized, or there may be no improvements needed based on the job description.');
        setLoading(false);
        return;
      }

      // Store in sessionStorage and navigate to review
      sessionStorage.setItem('resumeData', JSON.stringify(parseResponse.data));
      sessionStorage.setItem('suggestions', JSON.stringify(rewriteResponse.data));
      sessionStorage.setItem('evidenceMap', JSON.stringify(evidenceResponse.data));
      sessionStorage.setItem('jdSignals', JSON.stringify(jdResponse.data));
      sessionStorage.setItem('resumeFileName', resumeFile.name);

      router.push('/review');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-xl rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ATS-Approved Resume Optimizer
          </h1>
          <p className="text-gray-600 mb-8">
            Upload your resume and job description to get AI-powered optimization suggestions
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Resume (DOCX)
              </label>
              <input
                type="file"
                accept=".docx"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Description
              </label>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Paste the job description here..."
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Processing...' : 'Analyze Resume'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
