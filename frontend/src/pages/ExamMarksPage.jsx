/**
 * EduSync — Exam Marks Entry Page.
 * Select exam, then bulk-enter marks for students.
 */
import { useState, useEffect } from 'react';
import api from '../api';

export default function ExamMarksPage() {
    const [exams, setExams] = useState([]);
    const [selectedExam, setSelectedExam] = useState('');
    const [students, setStudents] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [marks, setMarks] = useState({});
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Load exams on mount
    useEffect(() => {
        api.get('/exams/list/').then(res => setExams(res.data.results || [])).catch(console.error);
    }, []);

    // Load students when exam selected
    useEffect(() => {
        if (!selectedExam) return;
        // Get students for the exam's class
        api.get('/auth/students/', { params: { page_size: 100 } })
            .then(res => setStudents(res.data.results || []))
            .catch(console.error);
    }, [selectedExam]);

    const handleMarkChange = (studentId, subjectId, field, value) => {
        const key = `${studentId}_${subjectId}`;
        setMarks(prev => ({
            ...prev,
            [key]: { ...prev[key], student_id: studentId, subject_id: subjectId, [field]: value },
        }));
    };

    const handleSubmit = async () => {
        setMessage('');
        setError('');
        setSubmitting(true);

        const marksArray = Object.values(marks).filter(
            m => m.marks_obtained !== undefined && m.marks_obtained !== ''
        ).map(m => ({
            student_id: m.student_id,
            subject_id: m.subject_id,
            marks_obtained: String(m.marks_obtained),
            max_marks: String(m.max_marks || '100'),
        }));

        if (marksArray.length === 0) {
            setError('No marks entered.');
            setSubmitting(false);
            return;
        }

        try {
            const { data } = await api.post('/exams/marks/bulk/', {
                exam_id: selectedExam,
                marks: marksArray,
            });
            setMessage(data.message || `${data.count} marks submitted!`);
            setMarks({});
        } catch (err) {
            setError(err.response?.data?.message || err.response?.data?.detail || 'Submission failed.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="page">
            <h1>📝 Exam Marks Entry</h1>

            <div className="filters">
                <label>Select Exam:</label>
                <select value={selectedExam} onChange={(e) => setSelectedExam(e.target.value)}>
                    <option value="">-- Select Exam --</option>
                    {exams.map(ex => (
                        <option key={ex.id} value={ex.id}>
                            {ex.exam_type_name} — {ex.class_name} ({ex.branch_name})
                        </option>
                    ))}
                </select>

                <label style={{ marginLeft: '1rem' }}>Subject ID (manual):</label>
                <input
                    type="text"
                    placeholder="Paste Subject UUID"
                    onChange={(e) => setSubjects([{ id: e.target.value, name: 'Subject' }])}
                    style={{ width: '280px' }}
                />
            </div>

            {message && <div className="success-msg">{message}</div>}
            {error && <div className="error-msg">{error}</div>}

            {selectedExam && students.length > 0 && subjects.length > 0 && (
                <>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Admission #</th>
                                <th>Student Name</th>
                                <th>Marks Obtained</th>
                                <th>Max Marks</th>
                            </tr>
                        </thead>
                        <tbody>
                            {students.map(s => (
                                subjects.map(sub => (
                                    <tr key={`${s.id}_${sub.id}`}>
                                        <td>{s.admission_number}</td>
                                        <td>{s.full_name || `${s.first_name} ${s.last_name}`}</td>
                                        <td>
                                            <input
                                                type="number"
                                                min="0"
                                                placeholder="0"
                                                value={marks[`${s.id}_${sub.id}`]?.marks_obtained || ''}
                                                onChange={(e) => handleMarkChange(s.id, sub.id, 'marks_obtained', e.target.value)}
                                            />
                                        </td>
                                        <td>
                                            <input
                                                type="number"
                                                min="0"
                                                placeholder="100"
                                                value={marks[`${s.id}_${sub.id}`]?.max_marks || '100'}
                                                onChange={(e) => handleMarkChange(s.id, sub.id, 'max_marks', e.target.value)}
                                            />
                                        </td>
                                    </tr>
                                ))
                            ))}
                        </tbody>
                    </table>

                    <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
                        {submitting ? 'Submitting...' : '✅ Submit All Marks'}
                    </button>
                </>
            )}

            {selectedExam && students.length === 0 && <p>No students found for this branch.</p>}
            {selectedExam && subjects.length === 0 && <p className="info-msg">Enter a Subject UUID above to load the marks grid.</p>}
        </div>
    );
}
