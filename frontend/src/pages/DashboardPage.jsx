/**
 * EduSync — Dashboard Page.
 */
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
    const { user } = useAuth();

    return (
        <div className="page">
            <h1>Dashboard</h1>
            <div className="card">
                <h3>Welcome, {user?.full_name} 👋</h3>
                <p><strong>Email:</strong> {user?.email}</p>
                <p><strong>Role:</strong> {user?.role_type}</p>
                <p><strong>Branch:</strong> {user?.branch || 'Global (Superadmin)'}</p>
            </div>
            <div className="quick-links">
                <h3>Quick Links</h3>
                <div className="grid">
                    <a href="/students" className="card link-card">👨‍🎓 Students</a>
                    <a href="/exam-marks" className="card link-card">📝 Exam Marks</a>
                    <a href="/report-card" className="card link-card">📊 Report Card</a>
                    <a href="/assessments" className="card link-card">📋 Assessments</a>
                </div>
            </div>
        </div>
    );
}
