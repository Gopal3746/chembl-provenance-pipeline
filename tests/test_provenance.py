import hashlib

from drug_catalog.provenance import calculate_sha256


def test_calculate_sha256(tmp_path) -> None:
    file_path = tmp_path / "sample.json"
    content = b'{"hello": "world"}'

    file_path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert calculate_sha256(file_path) == expected
