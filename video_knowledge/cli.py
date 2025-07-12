#!/usr/bin/env python3

import click
import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.logging import RichHandler

from .config import DATABASE_PATH, WHISPER_MODEL, LOG_LEVEL
from .database import VideoDatabase
from .processors import YouTubeProcessor, LocalProcessor, M3U8Processor

console = Console()

@click.group()
@click.option('--db-path', default=DATABASE_PATH, help='Path to SQLite database')
@click.option('--model', default=WHISPER_MODEL, help='Whisper model to use')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually processing')
@click.pass_context
def cli(ctx, db_path, model, verbose, dry_run):
    """Video Knowledge CLI - Extract and store video content from various sources."""
    ctx.ensure_object(dict)

    # Setup logging
    log_level_map = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }

    base_level = log_level_map.get(LOG_LEVEL.upper(), 20)
    log_level = max(10, base_level - verbose * 10)  # DEBUG=10, INFO=20, etc.

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

    ctx.obj['db'] = VideoDatabase(db_path)
    ctx.obj['model'] = model
    ctx.obj['dry_run'] = dry_run
    ctx.obj['verbose'] = verbose

@cli.command()
@click.argument('url')
@click.pass_context
def youtube(ctx, url):
    """Process a single YouTube video."""
    db = ctx.obj['db']
    dry_run = ctx.obj['dry_run']

    if dry_run:
        console.print(f"[yellow]Would process YouTube URL:[/yellow] {url}")
        return

    processor = YouTubeProcessor()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing YouTube video...", total=None)
        try:
            processor.process_video(url, db)
            progress.update(task, completed=True)
            console.print("[green]✓ YouTube video processed successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error processing YouTube video: {e}[/red]")
            sys.exit(1)

@cli.command()
@click.argument('path')
@click.pass_context
def local(ctx, path):
    """Process a local video file."""
    db = ctx.obj['db']
    dry_run = ctx.obj['dry_run']

    path_obj = Path(path)
    if not path_obj.exists():
        console.print(f"[red]✗ File not found: {path}[/red]")
        sys.exit(1)

    if dry_run:
        console.print(f"[yellow]Would process local file:[/yellow] {path}")
        return

    processor = LocalProcessor()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing local video...", total=None)
        try:
            processor.process_video(str(path_obj.absolute()), db)
            progress.update(task, completed=True)
            console.print("[green]✓ Local video processed successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error processing local video: {e}[/red]")
            sys.exit(1)

@cli.command()
@click.argument('url')
@click.pass_context
def m3u8(ctx, url):
    """Process an M3U8 stream."""
    db = ctx.obj['db']
    dry_run = ctx.obj['dry_run']

    if dry_run:
        console.print(f"[yellow]Would process M3U8 stream:[/yellow] {url}")
        return

    processor = M3U8Processor()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing M3U8 stream...", total=None)
        try:
            processor.process_video(url, db)
            progress.update(task, completed=True)
            console.print("[green]✓ M3U8 stream processed successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error processing M3U8 stream: {e}[/red]")
            sys.exit(1)

@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.pass_context
def process(ctx, config_file):
    """Process videos from a YAML configuration file."""
    import yaml

    db = ctx.obj['db']
    dry_run = ctx.obj['dry_run']

    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        console.print(f"[red]✗ Error reading YAML config: {e}[/red]")
        sys.exit(1)

    if not config or 'videos' not in config:
        console.print(f"[red]✗ Invalid YAML config: missing 'videos' section[/red]")
        sys.exit(1)

    videos = config['videos']

    # Count total videos to process
    total_videos = 0
    if 'youtube' in videos:
        total_videos += len(videos['youtube'])
    if 'local' in videos:
        total_videos += len(videos['local'])
    if 'm3u8' in videos:
        total_videos += len(videos['m3u8'])

    if dry_run:
        console.print(f"[yellow]Would process {total_videos} videos from {config_file}[/yellow]")
        if 'youtube' in videos:
            for video in videos['youtube']:
                console.print(f"  [blue]YouTube:[/blue] {video['url']}")
        if 'local' in videos:
            for video in videos['local']:
                console.print(f"  [blue]Local:[/blue] {video['path']}")
        if 'm3u8' in videos:
            for video in videos['m3u8']:
                console.print(f"  [blue]M3U8:[/blue] {video['url']}")
        return

    console.print(f"[blue]Processing {total_videos} videos from {config_file}...[/blue]")

    success_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing videos...", total=total_videos)

        # Process YouTube videos
        if 'youtube' in videos:
            processor = YouTubeProcessor()
            for video in videos['youtube']:
                try:
                    url = video['url']
                    custom_title = video.get('title')
                    processor.process_video_with_title(url, db, custom_title)
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]✗ Error processing YouTube video {video['url']}: {e}[/red]")
                    error_count += 1
                progress.advance(task)

        # Process local videos
        if 'local' in videos:
            processor = LocalProcessor()
            for video in videos['local']:
                try:
                    path = video['path']
                    custom_title = video.get('title')
                    processor.process_video_with_title(path, db, custom_title)
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]✗ Error processing local video {video['path']}: {e}[/red]")
                    error_count += 1
                progress.advance(task)

        # Process M3U8 streams
        if 'm3u8' in videos:
            processor = M3U8Processor()
            for video in videos['m3u8']:
                try:
                    url = video['url']
                    title = video.get('title')
                    order = video.get('order', 1)
                    processor.process_video_with_title(url, db, title, order)
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]✗ Error processing M3U8 stream {video['url']}: {e}[/red]")
                    error_count += 1
                progress.advance(task)

    # Summary
    table = Table(title="Processing Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Successful", str(success_count), style="green")
    table.add_row("Errors", str(error_count), style="red")
    table.add_row("Total", str(total_videos), style="blue")

    console.print(table)

@cli.command()
@click.option('--db-path', default=DATABASE_PATH, help='Path to SQLite database')
def stats(db_path):
    """Show database statistics."""
    db = VideoDatabase(db_path)

    try:
        videos = list(db.db['videos'].rows)
        video_count = len(videos)
        console.print(f"[blue]Total videos in database:[/blue] {video_count}")

        if video_count > 0:
            latest = videos[-1]
            console.print(f"[blue]Latest video:[/blue] {latest['title']}")
    except Exception as e:
        console.print(f"[red]✗ Error getting stats: {e}[/red]")

@cli.command()
@click.option('--port', default=8001, help='Port for Datasette server')
def view(port):
    """Launch Datasette GUI to view knowledge database."""
    import shutil
    
    if not shutil.which('datasette'):
        console.print("[red]✗ Datasette not found. Install with:[/red]")
        console.print("[yellow]  pip install datasette[/yellow]")
        return

    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        console.print("[red]✗ No knowledge database found. Process some videos first![/red]")
        return

    try:
        import subprocess
        subprocess.run([
            'datasette', 
            str(db_path), 
            '--port', str(port),
            '-o'
        ])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]✗ Error starting Datasette: {e}[/red]")

if __name__ == '__main__':
    cli()
