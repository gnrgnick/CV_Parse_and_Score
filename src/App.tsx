/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Navigation/Layout';
import { Dashboard } from './screens/Dashboard';
import { NewContacts } from './screens/NewContacts';
import { Errors } from './screens/Errors';
import { Alerts } from './screens/Alerts';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Live, wired to the cv-engine backend. Everything else is still mock-only. */}
        <Route path="/" element={<Layout><NewContacts /></Layout>} />
        <Route path="/contacts" element={<Layout><NewContacts /></Layout>} />
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/errors" element={<Layout><Errors /></Layout>} />
        <Route path="/alerts" element={<Layout><Alerts /></Layout>} />

        {/* Secondary navigation routes handled for demo purposes */}
        <Route path="/feed" element={<Layout><NewContacts /></Layout>} />
        <Route path="/logs" element={<Layout><Errors /></Layout>} />
        <Route path="/queue" element={<Layout><NewContacts /></Layout>} />
        <Route path="/archive" element={<Layout><Dashboard /></Layout>} />
        <Route path="/settings" element={<Layout><Alerts /></Layout>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
