import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">AI-Enhanced IDS Dashboard</h1>
        <p className="mt-2 text-slate-400">Real-time network traffic monitoring, ML detection, alerts, and security reports.</p>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4">Main Output Dashboard</h2>
          <ul className="space-y-3 text-slate-300">
            <li>Real-time network traffic monitoring</li>
            <li>Live detection of suspicious activities</li>
            <li>Security status overview</li>
            <li>Intrusion statistics and charts</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4">Detection Output</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-300">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="px-3 py-2">Source IP</th>
                  <th className="px-3 py-2">Destination IP</th>
                  <th className="px-3 py-2">Attack Type</th>
                  <th className="px-3 py-2">Severity</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-800">
                  <td className="px-3 py-3">192.168.1.10</td>
                  <td className="px-3 py-3">10.0.0.5</td>
                  <td className="px-3 py-3">DoS Attack</td>
                  <td className="px-3 py-3">High</td>
                  <td className="px-3 py-3">Detected</td>
                </tr>
                <tr>
                  <td className="px-3 py-3">192.168.1.15</td>
                  <td className="px-3 py-3">10.0.0.8</td>
                  <td className="px-3 py-3">Normal Traffic</td>
                  <td className="px-3 py-3">Low</td>
                  <td className="px-3 py-3">Safe</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4">Alert Output</h2>
          <div className="rounded-xl bg-slate-950 p-5">
            <p className="text-lg font-semibold text-amber-300">⚠ ALERT GENERATED</p>
            <div className="mt-4 text-slate-300 space-y-2">
              <p><strong>Threat Type:</strong> DDoS Attack</p>
              <p><strong>Source IP:</strong> 192.168.1.10</p>
              <p><strong>Severity:</strong> High</p>
              <p><strong>Detection Time:</strong> 10-Jun-2026 08:45 PM</p>
            </div>
            <div className="mt-4 rounded-xl bg-slate-900 p-4 text-slate-300">
              <p className="font-semibold">Recommended Action:</p>
              <p>Block Source IP and investigate network logs.</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4">Machine Learning Output</h2>
          <div className="space-y-3 text-slate-300">
            <p className="text-lg font-semibold">Prediction Result: Intrusion Detected</p>
            <p><strong>Attack Category:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li>DoS</li>
              <li>Probe</li>
              <li>R2L</li>
              <li>U2R</li>
              <li>Malware</li>
              <li>Normal Traffic</li>
            </ul>
            <p><strong>Confidence Score:</strong> 97.8%</p>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <h2 className="text-xl font-semibold mb-4">Reports</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-950 p-4 text-slate-300">
            <p className="font-semibold">Daily Security Report</p>
            <p className="mt-2">Generated and available for the latest 24-hour window.</p>
          </div>
          <div className="rounded-xl bg-slate-950 p-4 text-slate-300">
            <p className="font-semibold">Weekly Threat Analysis</p>
            <p className="mt-2">Weekly summary of attack trends and risk posture.</p>
          </div>
          <div className="rounded-xl bg-slate-950 p-4 text-slate-300">
            <p className="font-semibold">Attack Trend Graphs</p>
            <p className="mt-2">Visual summaries of traffic and intrusion patterns.</p>
          </div>
          <div className="rounded-xl bg-slate-950 p-4 text-slate-300">
            <p className="font-semibold">Top Malicious IP Addresses</p>
            <p className="mt-2">192.168.1.10, 10.1.1.202, 172.16.0.15</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

