import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_should_process_async_small_file():
    from ingestion.utils.task_manager import should_process_async
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Small doc")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    path = Path(tmp.name)
    try:
        assert not should_process_async(path)
    finally:
        path.unlink(missing_ok=True)


def test_get_task_status_mock():
    from ingestion.utils.task_manager import get_task_status, TaskStatus
    from unittest.mock import patch

    with patch("celery.result.AsyncResult") as mock_result:
        mock_result.return_value.state = "PENDING"
        status = get_task_status("fake_id")
        assert status["status"] == TaskStatus.PENDING
