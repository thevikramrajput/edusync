/**
 * EduSync — Student Detail Page.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';

export default function StudentDetailPage() {
    const { id } = useParams();
    const [student, setStudent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        api.get(`/auth/students/${id}/`)
            .then(res => setStudent(res.data))
            .catch(err => setError(err.response?.data?.detail || 'Student not found.'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <div className="page"><p>Loading...</p></div>;
    if (error) return <div className="page"><div className="error-msg">{error}</div></div>;

    return (
        <div className="page">
            <Link to="/students" className="back-link">← Back to Students</Link>
            <h1>{student.full_name || `${student.first_name} ${student.last_name}`}</h1>

            <div className="card">
                <div className="detail-grid">
                    <div><strong>Admission #:</strong> {student.admission_number}</div>
                    <div><strong>Email:</strong> {student.email || '—'}</div>
                    <div><strong>Class:</strong> {student.class_name || '—'}</div>
                    <div><strong>Section:</strong> {student.section_name || '—'}</div>
                    <div><strong>Branch:</strong> {student.branch_name || '—'}</div>
                    <div><strong>Date of Birth:</strong> {student.date_of_birth || '—'}</div>
                    <div><strong>Guardian Name:</strong> {student.guardian_name || '—'}</div>
                    <div><strong>Guardian Phone:</strong> {student.guardian_phone || '—'}</div>
                </div>
            </div>

            <div className="quick-links">
                <h3>Actions</h3>
                <div className="grid">
                    <Link to={`/report-card?student_id=${id}`} className="card link-card">📊 Report Card</Link>
                    <Link to={`/assessments?student_id=${id}`} className="card link-card">📋 Assessments</Link>
                </div>
            </div>
        </div>
    );
}
