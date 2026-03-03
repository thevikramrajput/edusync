/**
 * EduSync — Assessment Entry Page.
 * Create assessments with criteria scores, submit, approve.
 */
import { useState, useEffect } from 'react';
import api from '../api';

export default function AssessmentPage() {
    const [assessments, setAssessments] = useState([]);
    const [types, setTypes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    // Create form
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({
        student: '', academic_year: '', quarter: '',
        assessment_type: '', scores: [],
    });
    const [criteria, setCriteria] = useState([]);

    useEffect(() => {
        fetchAssessments();
        api.get('/assessments/types/').then(res => setTypes(res.data.results || [])).catch(console.error);
    }, []);

    const fetchAssessments = () => {
        setLoading(true);
        api.get('/assessments/student/')
            .then(res => setAssessments(res.data.results || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    // Load criteria tree when type selected
    const loadCriteria = async (typeId) => {
        if (!typeId) { setCriteria([]); return; }
        try {
            const { data } = await api.get(`/assessments/types/${typeId}/`);
            const allCriteria = [];
            (data.areas || []).forEach(area => {
                (area.sub_areas || []).forEach(sub => {
                    (sub.criteria || []).forEach(c => {
                        allCriteria.push({
                            id: c.id,
                            label: `${area.name} → ${sub.name}: ${c.description}`,
                            max_score: c.max_score,
                            score: 0,
                        });
                    });
                });
            });
            setCriteria(allCriteria);
        } catch (err) {
            console.error('Failed to load criteria:', err);
        }
    };

    const handleScoreChange = (criteriaId, value) => {
        setCriteria(prev => prev.map(c =>
            c.id === criteriaId ? { ...c, score: parseInt(value) || 0 } : c
        ));
    };

    const handleCreate = async () => {
        setError('');
        setMessage('');
        const scores = criteria.map(c => ({
            criteria_id: c.id,
            score: c.score,
        }));
        try {
            await api.post('/assessments/student/', {
                ...form,
                scores,
            });
            setMessage('Assessment created successfully!');
            setShowForm(false);
            fetchAssessments();
        } catch (err) {
            setError(err.response?.data?.message || JSON.stringify(err.response?.data) || 'Create failed.');
        }
    };

    const handleAction = async (id, action) => {
        setError('');
        setMessage('');
        try {
            const { data } = await api.post(`/assessments/student/${id}/${action}/`);
            setMessage(data.message || `${action} successful!`);
            fetchAssessments();
        } catch (err) {
            setError(err.response?.data?.message || `${action} failed.`);
        }
    };

    return (
        <div className="page">
            <div className="page-header">
                <h1>📋 Assessments</h1>
                <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
                    {showForm ? 'Cancel' : '+ New Assessment'}
                </button>
            </div>

            {message && <div className="success-msg">{message}</div>}
            {error && <div className="error-msg">{error}</div>}

            {/* Create Form */}
            {showForm && (
                <div className="card form-card">
                    <h3>New Assessment</h3>
                    <div className="form-grid">
                        <div>
                            <label>Student ID</label>
                            <input value={form.student} onChange={e => setForm({ ...form, student: e.target.value })} placeholder="Student UUID" />
                        </div>
                        <div>
                            <label>Academic Year ID</label>
                            <input value={form.academic_year} onChange={e => setForm({ ...form, academic_year: e.target.value })} placeholder="Academic Year UUID" />
                        </div>
                        <div>
                            <label>Quarter ID</label>
                            <input value={form.quarter} onChange={e => setForm({ ...form, quarter: e.target.value })} placeholder="Quarter UUID" />
                        </div>
                        <div>
                            <label>Assessment Type</label>
                            <select value={form.assessment_type} onChange={e => {
                                setForm({ ...form, assessment_type: e.target.value });
                                loadCriteria(e.target.value);
                            }}>
                                <option value="">-- Select --</option>
                                {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                            </select>
                        </div>
                    </div>

                    {criteria.length > 0 && (
                        <>
                            <h4>Criteria Scores</h4>
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Criteria</th>
                                        <th>Max</th>
                                        <th>Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {criteria.map(c => (
                                        <tr key={c.id}>
                                            <td>{c.label}</td>
                                            <td>{c.max_score}</td>
                                            <td>
                                                <input
                                                    type="number"
                                                    min="0"
                                                    max={c.max_score}
                                                    value={c.score}
                                                    onChange={e => handleScoreChange(c.id, e.target.value)}
                                                    style={{ width: '60px' }}
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    )}

                    <button className="btn-primary" onClick={handleCreate} style={{ marginTop: '1rem' }}>
                        Create Assessment
                    </button>
                </div>
            )}

            {/* Existing Assessments List */}
            {loading ? <p>Loading...</p> : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Type</th>
                            <th>Quarter</th>
                            <th>Status</th>
                            <th>Scores</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {assessments.length === 0 ? (
                            <tr><td colSpan="6" className="empty">No assessments found.</td></tr>
                        ) : (
                            assessments.map(a => (
                                <tr key={a.id}>
                                    <td>{a.student_name} ({a.admission_number})</td>
                                    <td>{a.assessment_type_name}</td>
                                    <td>{a.quarter_name}</td>
                                    <td><span className={`status-badge status-${a.status.toLowerCase()}`}>{a.status}</span></td>
                                    <td>{a.scores?.length || 0} entries</td>
                                    <td>
                                        {a.status === 'DRAFT' && (
                                            <button className="btn-sm btn-submit" onClick={() => handleAction(a.id, 'submit')}>Submit</button>
                                        )}
                                        {a.status === 'SUBMITTED' && (
                                            <button className="btn-sm btn-approve" onClick={() => handleAction(a.id, 'approve')}>Approve</button>
                                        )}
                                        {a.status === 'APPROVED' && <span className="approved-badge">✓ Done</span>}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            )}
        </div>
    );
}
