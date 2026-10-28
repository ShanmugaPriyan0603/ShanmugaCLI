from planner.models import StudyLog, Subject
from planner.storage import JsonStore
from planner.study_engine import add_subject, log_session, progress


def test_logging_updates_subject_hours(tmp_path):
    store = JsonStore(tmp_path)
    subject = add_subject(store, Subject(name="Physics"))
    log_session(store, StudyLog(subject_id=subject.id, minutes=45))
    assert store.load("subjects")[0]["completed_hours"] == 0.75
    assert progress(store)[0]["completed_hours"] == 0.75
