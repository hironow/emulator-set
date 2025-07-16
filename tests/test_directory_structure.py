import os
import glob


def test_tests_directory_exists():
    """Test that tests directory exists."""
    # Check from parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tests_path = os.path.join(parent_dir, "tests")
    assert os.path.exists(tests_path), "tests directory should exist"
    assert os.path.isdir(tests_path), "tests should be a directory"


def test_all_test_files_in_tests_directory():
    """Test that all test_*.py files are in the tests directory."""
    # Get parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check that no test files exist in root directory
    root_test_files = glob.glob(os.path.join(parent_dir, "test_*.py"))
    assert len(root_test_files) == 0, f"Test files found in root directory: {root_test_files}"
    
    # Check that test files exist in tests directory
    tests_dir_files = glob.glob(os.path.join(parent_dir, "tests", "test_*.py"))
    expected_test_files = [
        "test_elasticsearch_emulator.py",
        "test_firebase_emulator.py",
        "test_github_actions.py",
        "test_neo4j_emulator.py",
        "test_pgadapter_emulator.py",
        "test_qdrant_emulator.py",
        "test_spanner_emulator.py",
        "test_a2a_inspector.py",
        "test_directory_structure.py"
    ]
    
    tests_dir_basenames = [os.path.basename(f) for f in tests_dir_files]
    for test_file in expected_test_files:
        assert test_file in tests_dir_basenames, f"{test_file} should be in tests directory"