import os

def test_smoke_project_manifest_exists():
    root = os.path.dirname(os.path.dirname(__file__))
    manifest = os.path.join(root, 'scaffold', 'template_manifest.json')
    assert os.path.exists(manifest)

def test_smoke_schema_exists():
    root = os.path.dirname(os.path.dirname(__file__))
    schema = os.path.join(root, 'schema', 'schema.sql')
    assert os.path.exists(schema)
