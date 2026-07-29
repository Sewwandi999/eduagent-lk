from src.schemas import OutputType, StudentLevel, TeacherRequest


def test_teacher_request_validation():
    request = TeacherRequest(
        grade=9,
        topic="Reported Speech",
        duration_minutes=45,
        student_level=StudentLevel.AVERAGE,
        output_type=OutputType.LESSON_PLAN,
    )
    assert request.grade == 9
    assert request.task_id
