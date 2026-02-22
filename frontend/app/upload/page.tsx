'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';

type ProcessingStep = 'idle' | 'parse' | 'jd' | 'evidence' | 'rewrite' | 'done' | 'error';

export default function UploadPage() {
  const router = useRouter();
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState<ProcessingStep>('idle');

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

    setError('');
    setProcessing('parse');

    try {
      const formData = new FormData();
      formData.append('file', resumeFile);

      const parseResponse = await axios.post('/api/parse/docx', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setProcessing('jd');
      const jdResponse = await axios.post('/api/jd/extract', { text: jdText });

      setProcessing('evidence');
      const evidenceResponse = await axios.post('/api/evidence/map', {
        jd_signals: jdResponse.data,
        resume_json: parseResponse.data,
      });

      setProcessing('rewrite');
      const rewriteResponse = await axios.post('/api/rewrite/suggest', {
        jd_signals: jdResponse.data,
        evidence_map: evidenceResponse.data,
        resume_json: parseResponse.data,
        max_suggestions: 10,
      });

      setProcessing('done');

      if (!parseResponse.data.content_units?.length) {
        setError('No content units found in resume.');
        setProcessing('error');
        return;
      }

      if (!rewriteResponse.data.suggestions?.length) {
        setError('No suggestions were generated. Your resume may already be well-optimized.');
        setProcessing('error');
        return;
      }

      sessionStorage.setItem('resumeData', JSON.stringify(parseResponse.data));
      sessionStorage.setItem('suggestions', JSON.stringify(rewriteResponse.data));
      sessionStorage.setItem('evidenceMap', JSON.stringify(evidenceResponse.data));
      sessionStorage.setItem('jdSignals', JSON.stringify(jdResponse.data));
      sessionStorage.setItem('resumeFileName', resumeFile.name);

      router.push('/review');
    } catch (err: unknown) {
      let msg = 'An error occurred. Please try again.';
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        if (data?.detail) msg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        else if (err.response?.status === 500) msg = 'Server error. Check the backend terminal for details.';
      }
      setError(msg);
      setProcessing('error');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file?.name.endsWith('.docx')) {
      setResumeFile(file);
      setError('');
    } else if (file) {
      setError('Only .docx files are supported');
      setResumeFile(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file?.name.endsWith('.docx')) {
      setResumeFile(file);
      setError('');
    } else if (file) {
      setError('Only .docx files are supported');
      setResumeFile(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  // Processing / loading view
  if (processing !== 'idle') {
    const steps = [
      { key: 'parse', label: 'Extracting Resume Content', desc: 'Reading your resume and identifying key sections' },
      { key: 'jd', label: 'Analyzing Job Description', desc: 'Understanding required skills and keywords' },
      { key: 'rewrite', label: 'Optimizing Bullet Points', desc: 'Rewriting content to match ATS requirements' },
    ];
    const currentIdx = processing === 'parse' ? 0 : processing === 'jd' || processing === 'evidence' ? 1 : processing === 'rewrite' ? 2 : 2;
    const progress = processing === 'done' || processing === 'error' ? 100 : ((currentIdx + (processing === 'parse' ? 0.33 : processing === 'jd' || processing === 'evidence' ? 0.66 : 1)) / 3) * 100;

    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-10">
            <div className="w-16 h-16 rounded-full bg-purple-500 flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl font-bold text-white">C</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Optimizing Your Resume</h1>
            <p className="text-gray-500 mt-1">{resumeFile?.name || 'resume.docx'}</p>
          </div>

          <div className="mb-8">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2 text-center">{Math.round(progress)}% Complete</p>
          </div>

          <div className="space-y-4 mb-8">
            {steps.map((step, i) => {
              const status = i < currentIdx ? 'done' : i === currentIdx && processing !== 'error' ? 'active' : 'pending';
              return (
                <div
                  key={step.key}
                  className={`rounded-lg p-4 flex items-center gap-4 ${
                    status === 'done' ? 'bg-green-50' : status === 'active' ? 'bg-blue-50' : 'bg-white border border-gray-200'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                      status === 'done' ? 'bg-green-500' : status === 'active' ? 'bg-blue-500' : 'bg-gray-200'
                    }`}
                  >
                    {status === 'done' ? (
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : status === 'active' ? (
                      <svg className="w-6 h-6 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className={`font-semibold ${status === 'done' ? 'text-green-800' : status === 'active' ? 'text-blue-800' : 'text-gray-500'}`}>
                      {step.label}
                    </p>
                    <p className={`text-sm ${status === 'done' ? 'text-green-600' : status === 'active' ? 'text-blue-600' : 'text-gray-400'}`}>
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {processing === 'error' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
              <button
                onClick={() => setProcessing('idle')}
                className="mt-3 block text-sm font-medium underline"
              >
                Try again
              </button>
            </div>
          )}

          <div className="bg-purple-50 rounded-lg p-4 flex gap-3">
            <svg className="w-6 h-6 text-yellow-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
            </svg>
            <div>
              <p className="font-semibold text-purple-800">Did you know?</p>
              <p className="text-sm text-purple-700 mt-1">
                About 75% of resumes are rejected by ATS systems before a human ever sees them. Optimizing your resume can significantly increase your chances!
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </Link>

        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-purple-700">ATS Resume Optimizer</h1>
          <p className="mt-2 text-gray-600">
            Upload your resume and job description to create an ATS-approved version.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Resume Upload Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Upload Resume (DOCX)
            </label>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                dragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="file"
                accept=".docx"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                required
              />
              <div className="flex flex-col items-center gap-2">
                <svg
                  className="w-12 h-12 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-gray-600">
                  {resumeFile ? (
                    <span className="font-medium text-purple-600">{resumeFile.name}</span>
                  ) : (
                    <>
                      Drag and drop your resume here, or{' '}
                      <span className="text-purple-600 font-medium">click to browse</span>
                    </>
                  )}
                </p>
                <p className="text-sm text-gray-400">Only .docx files are supported</p>
              </div>
            </div>
          </div>

          {/* Job Description Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Job Description
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={12}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="Paste the job description here..."
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              The AI will optimize your resume to match this job description.
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full py-4 px-6 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold text-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            Start Optimizing
          </button>
        </form>
      </div>
    </div>
  );
}
