from app.evidence import EvidenceStore


def test_evidence_store_writes_and_reads_atomically(tmp_path):
    store = EvidenceStore(tmp_path)
    package = {
        "execution_id": "EXEC-TEST-001",
        "status": "RECORDED",
        "request_hash": "abc",
        "response_hash": "def",
    }

    uri = store.write("EXEC-TEST-001", package)

    assert uri.startswith("file:")
    assert store.read("EXEC-TEST-001") == package
    assert not (tmp_path / ".EXEC-TEST-001.json.tmp").exists()


def test_evidence_store_rejects_path_traversal(tmp_path):
    store = EvidenceStore(tmp_path)

    try:
        store.write("../escape", {"status": "RECORDED"})
    except ValueError:
        pass
    else:
        raise AssertionError("EvidenceStore must reject path traversal")
