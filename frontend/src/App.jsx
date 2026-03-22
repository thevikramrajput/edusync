/**
 * EduSync — App Root.
 * Routes: login (public), everything else protected.
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StudentListPage from './pages/StudentListPage';
import StudentDetailPage from './pages/StudentDetailPage';
import ExamMarksPage from './pages/ExamMarksPage';
import ReportCardPage from './pages/ReportCardPage';
import AssessmentPage from './pages/AssessmentPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected — wrapped in Layout */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<DashboardPage />} />
            <Route path="students" element={<StudentListPage />} />
            <Route path="students/:id" element={<StudentDetailPage />} />
            <Route path="exam-marks" element={<ExamMarksPage />} />
            <Route path="report-card" element={<ReportCardPage />} />
            <Route path="assessments" element={<AssessmentPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
