#!/usr/bin/env python3

import click
import sys
import logging
import yaml
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.logging import RichHandler

from .config import DATABASE_PATH, WHISPER_MODEL, LOG_LEVEL
from .database import VideoDatabase
from .processors import YouTubeProcessor, LocalProcessor, M3U8Processor

console = Console()


def setup_logging(verbose):
    level = max(10, {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}.get(LOG_LEVEL.upper(), 20) - verbose * 10)
    logging.basicConfig(level=level, format="%(message)s", handlers=[RichHandler(console=console)])


def process_with_progress(processor, location, db, description):
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task(description, total=None)
        try:
            processor.process_video(location, db)
            progress.update(task, completed=True)
            console.print(f"[green]✓ {description.split()[-1].capitalize()} processed successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            sys.exit(1)


@click.group()
@click.option('--db-path', default=DATABASE_PATH, help='Database path')
@click.option('--model', default=WHISPER_MODEL, help='Whisper model')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--dry-run', is_flag=True, help='Preview only')
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx, db_path, model, verbose, dry_run):
    """vid2text CLI - Extract and store video transcription from various sources."""
    ctx.ensure_object(dict)
    setup_logging(verbose)
    ctx.obj.update({'db': VideoDatabase(db_path), 'dry_run': dry_run})


@cli.command()
@click.argument('url')
@click.pass_context
def youtube(ctx, url):
    """Process a YouTube video."""
    if ctx.obj['dry_run']:
        console.print(f"[yellow]Would process YouTube URL:[/yellow] {url}")
        return
    process_with_progress(YouTubeProcessor(), url, ctx.obj['db'], "Processing YouTube video...")


@cli.command()
@click.argument('path')
@click.pass_context
def local(ctx, path):
    """Process a local video file."""
    if not Path(path).exists():
        console.print(f"[red]✗ File not found: {path}[/red]")
        sys.exit(1)
    
    if ctx.obj['dry_run']:
        console.print(f"[yellow]Would process local file:[/yellow] {path}")
        return
    process_with_progress(LocalProcessor(), str(Path(path).absolute()), ctx.obj['db'], "Processing local video...")


@cli.command()
@click.argument('url')
@click.pass_context
def m3u8(ctx, url):
    """Process an M3U8 stream."""
    if ctx.obj['dry_run']:
        console.print(f"[yellow]Would process M3U8 stream:[/yellow] {url}")
        return
    process_with_progress(M3U8Processor(), url, ctx.obj['db'], "Processing M3U8 stream...")


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.pass_context
def process(ctx, config_file):
    """Process videos from a YAML configuration file."""
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        console.print(f"[red]✗ Error reading config: {e}[/red]")
        sys.exit(1)

    if not config or 'videos' not in config:
        console.print("[red]✗ Invalid config: missing 'videos' section[/red]")
        sys.exit(1)

    videos = config['videos']
    total_videos = sum(len(videos.get(k, [])) for k in ['youtube', 'local', 'm3u8'])
    
    if ctx.obj['dry_run']:
        console.print(f"[yellow]Would process {total_videos} videos from {config_file}[/yellow]")
        for section, items in videos.items():
            for item in items:
                url_or_path = item.get('url', item.get('path', ''))
                console.print(f"  [blue]{section.capitalize()}:[/blue] {url_or_path}")
        return

    console.print(f"[blue]Processing {total_videos} videos from {config_file}...[/blue]")
    success_count = error_count = 0
    processors = {'youtube': YouTubeProcessor(), 'local': LocalProcessor(), 'm3u8': M3U8Processor()}
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task("Processing videos...", total=total_videos)
        
        for section, items in videos.items():
            if section in processors:
                console.print(f"[blue]Processing {len(items)} {section} videos...[/blue]")
                for item in items:
                    location = item.get('url', item.get('path', ''))
                    try:
                        if section == 'youtube':
                            processors[section].process_video_with_title(item['url'], ctx.obj['db'], item.get('title'))
                        elif section == 'local':
                            processors[section].process_video_with_title(item['path'], ctx.obj['db'], item.get('title'))
                        elif section == 'm3u8':
                            processors[section].process_video_with_title(item['url'], ctx.obj['db'], item.get('title'), item.get('order', 1))
                        success_count += 1
                    except Exception as e:
                        console.print(f"[red]✗ Error processing {location}: {e}[/red]")
                        error_count += 1
                    progress.advance(task)

    table = Table(title="Processing Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Successful", str(success_count), style="green")
    table.add_row("Errors", str(error_count), style="red")
    table.add_row("Total", str(total_videos), style="blue")
    console.print(table)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    try:
        db = ctx.obj['db']
        videos = list(db.db['videos'].rows)
        console.print(f"[blue]Total videos:[/blue] {len(videos)}")
        if videos:
            console.print(f"[blue]Latest:[/blue] {videos[-1]['title']}")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@cli.command()
@click.option('--port', default=8001, help='Port for Datasette server')
def view(port):
    """Launch Datasette GUI."""
    if not shutil.which('datasette'):
        console.print("[red]✗ Datasette not found. Install with: pip install datasette[/red]")
        return

    if not Path(DATABASE_PATH).exists():
        console.print("[red]✗ No database found. Process videos first![/red]")
        return

    try:
        subprocess.run(['datasette', DATABASE_PATH, '--port', str(port), '-o'])
    except (KeyboardInterrupt, Exception) as e:
        if not isinstance(e, KeyboardInterrupt):
            console.print(f"[red]✗ Error starting Datasette: {e}[/red]")


if __name__ == '__main__':
    cli()