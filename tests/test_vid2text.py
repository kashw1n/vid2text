import os
import tempfile
import pytest
import json
import yaml
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from vid2text.cli import cli
from vid2text.database import VideoDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = VideoDatabase(db_path)
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_config(tmpdir):
    """Create a sample configuration file for testing."""
    config_content = {
        'videos': {
            'youtube': [
                {'url': 'https://www.youtube.com/watch?v=test123'},
                {'url': 'https://www.youtube.com/watch?v=test456', 'title': 'Custom Title'}
            ],
            'local': [
                {'path': str(tmpdir.join('test_video.mp4'))},
                {'path': str(tmpdir.join('videos/folder'))},
            ],
            'm3u8': [
                {'url': 'https://example.com/stream.m3u8', 'title': 'Test Stream'}
            ]
        },
        'settings': {
            'whisper_model': 'small.en',
            'log_level': 'DEBUG'
        }
    }
    
    config_file = tmpdir.join('test_config.yaml')
    config_file.write(yaml.dump(config_content))
    return str(config_file)


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'vid2text CLI' in result.output


def test_youtube_dry_run():
    """Test YouTube command in dry-run mode."""
    runner = CliRunner()
    test_url = 'https://www.youtube.com/watch?v=test123'
    
    result = runner.invoke(cli, ['--dry-run', 'youtube', test_url])
    assert result.exit_code == 0
    assert 'Would process YouTube URL:' in result.output
    assert test_url in result.output


def test_local_dry_run(tmpdir):
    """Test local command in dry-run mode."""
    runner = CliRunner()
    
    # Create a dummy video file
    test_file = tmpdir.join('test_video.mp4')
    test_file.write('dummy video content')
    
    result = runner.invoke(cli, ['--dry-run', 'local', str(test_file)])
    assert result.exit_code == 0
    assert 'Would process local file:' in result.output
    # Check for the filename instead of full path due to Rich formatting
    assert 'test_video.mp4' in result.output


def test_local_file_not_found():
    """Test local command with non-existent file."""
    runner = CliRunner()
    
    result = runner.invoke(cli, ['local', '/non/existent/file.mp4'])
    assert result.exit_code == 1
    assert 'File not found:' in result.output


def test_m3u8_dry_run():
    """Test M3U8 command in dry-run mode."""
    runner = CliRunner()
    test_url = 'https://example.com/stream.m3u8'
    
    result = runner.invoke(cli, ['--dry-run', 'm3u8', test_url])
    assert result.exit_code == 0
    assert 'Would process M3U8 stream:' in result.output
    assert test_url in result.output


def test_process_config_dry_run(sample_config):
    """Test process command with config file in dry-run mode."""
    runner = CliRunner()
    
    result = runner.invoke(cli, ['--dry-run', 'process', sample_config])
    assert result.exit_code == 0
    assert 'Would process' in result.output
    assert 'videos from' in result.output


def test_process_config_invalid_file():
    """Test process command with invalid config file."""
    runner = CliRunner()
    
    result = runner.invoke(cli, ['process', '/non/existent/config.yaml'])
    assert result.exit_code == 2  # Click's exit code for file not found


def test_process_config_invalid_yaml(tmpdir):
    """Test process command with invalid YAML content."""
    runner = CliRunner()
    
    # Create invalid YAML file
    invalid_config = tmpdir.join('invalid.yaml')
    invalid_config.write('invalid: yaml: content: [')
    
    result = runner.invoke(cli, ['process', str(invalid_config)])
    assert result.exit_code == 1
    assert 'Error reading config:' in result.output


def test_process_config_missing_videos_section(tmpdir):
    """Test process command with config missing videos section."""
    runner = CliRunner()
    
    # Create config without videos section
    config_content = {'settings': {'whisper_model': 'small.en'}}
    config_file = tmpdir.join('no_videos.yaml')
    config_file.write(yaml.dump(config_content))
    
    result = runner.invoke(cli, ['process', str(config_file)])
    assert result.exit_code == 1
    assert "missing 'videos' section" in result.output


def test_stats_empty_database(temp_db):
    """Test stats command with empty database."""
    runner = CliRunner()
    
    result = runner.invoke(cli, ['--db-path', temp_db, 'stats'])
    assert result.exit_code == 0
    assert 'Total videos: 0' in result.output


def test_stats_with_data(temp_db):
    """Test stats command with data in database."""
    # Insert test data
    db = VideoDatabase(temp_db)
    test_video = {
        'id': 'test123',
        'title': 'Test Video',
        'content': 'This is a test transcription',
        'creator': 'Test Creator',
        'source': 'YouTube'
    }
    db.insert_video(test_video)
    
    runner = CliRunner()
    result = runner.invoke(cli, ['--db-path', temp_db, 'stats'])
    assert result.exit_code == 0
    assert 'Total videos: 1' in result.output
    assert 'Test Video' in result.output


def test_stats_database_error():
    """Test stats command with database error."""
    runner = CliRunner()
    
    # Use invalid database path
    result = runner.invoke(cli, ['--db-path', '/invalid/path/db.sqlite', 'stats'])
    assert result.exit_code == 1
    assert 'Error:' in result.output or result.exit_code == 1


@patch('vid2text.cli.shutil.which')
def test_view_datasette_not_found(mock_which):
    """Test view command when Datasette is not installed."""
    mock_which.return_value = None
    
    runner = CliRunner()
    result = runner.invoke(cli, ['view'])
    assert result.exit_code == 0
    assert 'Datasette not found' in result.output


@patch('vid2text.cli.Path.exists')
@patch('vid2text.cli.shutil.which')
def test_view_no_database(mock_which, mock_exists):
    """Test view command when database doesn't exist."""
    mock_which.return_value = '/usr/local/bin/datasette'
    mock_exists.return_value = False
    
    runner = CliRunner()
    result = runner.invoke(cli, ['view'])
    assert result.exit_code == 0
    assert 'No database found' in result.output


def test_cli_options():
    """Test CLI global options."""
    runner = CliRunner()
    
    # Test version option
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    
    # Test verbose option
    result = runner.invoke(cli, ['-v', '--help'])
    assert result.exit_code == 0


@patch('vid2text.processors.YouTubeProcessor.process_video')
def test_youtube_command_success(mock_process, temp_db):
    """Test successful YouTube video processing."""
    mock_process.return_value = None  # Simulate successful processing
    
    runner = CliRunner()
    result = runner.invoke(cli, ['--db-path', temp_db, 'youtube', 'https://www.youtube.com/watch?v=test123'])
    assert result.exit_code == 0
    assert 'processed successfully' in result.output or result.exit_code == 0


@patch('vid2text.processors.YouTubeProcessor.process_video')
def test_youtube_command_error(mock_process, temp_db):
    """Test YouTube video processing with error."""
    mock_process.side_effect = Exception("Test error")
    
    runner = CliRunner()
    result = runner.invoke(cli, ['--db-path', temp_db, 'youtube', 'https://www.youtube.com/watch?v=test123'])
    assert result.exit_code == 1
    assert 'Error:' in result.output


def test_transcription_without_whisper():
    """Test that transcription fails gracefully without Whisper packages."""
    from vid2text.transcription import Transcriber
    import tempfile
    
    # Create a dummy audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b'dummy audio content')
        audio_file = f.name
    
    try:
        # This should fail if no Whisper packages are installed
        with pytest.raises((ImportError, RuntimeError)):
            Transcriber.transcribe_audio(audio_file)
    finally:
        import os
        if os.path.exists(audio_file):
            os.unlink(audio_file)


def test_database_operations(temp_db):
    """Test basic database operations."""
    db = VideoDatabase(temp_db)
    
    # Test video insertion
    video_data = {
        'id': 'test123',
        'title': 'Test Video',
        'content': 'Test transcription content',
        'creator': 'Test Creator',
        'source': 'Test Source'
    }
    
    # Video should not exist initially
    assert not db.is_video_present('test123')
    
    # Insert video
    db.insert_video(video_data)
    
    # Video should now exist
    assert db.is_video_present('test123')
    
    # Test that video exists after insertion
    videos = list(db.db['videos'].rows)
    assert len(videos) == 1
    assert videos[0]['title'] == 'Test Video'


def test_database_validation_errors(temp_db):
    """Test database validation for required fields."""
    db = VideoDatabase(temp_db)
    
    # Test missing required fields
    incomplete_data = {
        'id': 'test123',
        # Missing title and content
    }
    
    with pytest.raises(ValueError) as excinfo:
        db.insert_video(incomplete_data)
    assert 'Missing required fields' in str(excinfo.value)


def test_config_environment_variables():
    """Test that configuration respects environment variables."""
    from vid2text.config import DATABASE_PATH, LOG_LEVEL, WHISPER_MODEL
    
    # These should have default values
    assert DATABASE_PATH is not None
    assert LOG_LEVEL is not None
    assert WHISPER_MODEL is not None


@pytest.mark.parametrize("command,args", [
    ("youtube", ["https://www.youtube.com/watch?v=test"]),
    ("local", ["/tmp/test.mp4"]),
    ("m3u8", ["https://example.com/stream.m3u8"]),
])
def test_dry_run_all_commands(command, args):
    """Test dry-run mode for all main commands."""
    runner = CliRunner()
    
    # For local command, create the file if it doesn't exist
    if command == "local":
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            args = [f.name]
        
        try:
            result = runner.invoke(cli, ['--dry-run', command] + args)
            assert result.exit_code == 0
            assert 'Would process' in result.output
        finally:
            os.unlink(args[0])
    else:
        result = runner.invoke(cli, ['--dry-run', command] + args)
        assert result.exit_code == 0
        assert 'Would process' in result.output


def test_custom_model_option(temp_db):
    """Test custom Whisper model option."""
    runner = CliRunner()
    
    result = runner.invoke(cli, [
        '--db-path', temp_db,
        '--model', 'tiny.en',
        '--dry-run',
        'youtube', 'https://www.youtube.com/watch?v=test'
    ])
    assert result.exit_code == 0


def test_verbose_option():
    """Test verbose logging option."""
    runner = CliRunner()
    
    result = runner.invoke(cli, ['-v', '--dry-run', 'youtube', 'https://www.youtube.com/watch?v=test'])
    assert result.exit_code == 0
    
    # Test multiple verbose flags
    result = runner.invoke(cli, ['-vv', '--dry-run', 'youtube', 'https://www.youtube.com/watch?v=test'])
    assert result.exit_code == 0