Edge-TTS Audiobook Converter

A Python command-line tool that converts EPUB and Text files into high-quality MP3 audiobooks using Microsoft Edge's Neural Text-to-Speech engine.
Features

    Multi-Format Support: Accepts both .txt and .epub files.

    Smart Chunking: Automatically splits large files into smaller text chunks to bypass character limits.

    Neural Voices: Uses high-quality en-US-JennyNeural voice (configurable in code).

    Auto-Concatenation: Merges all generated audio segments into a single, seamless MP3 file.

    Clean Output: Automatically sanitizes filenames (e.g., My Book - Vol 1.epub → My_Book_Vol_1.mp3) and deletes temporary chunk files after processing.

Prerequisites
System Requirements

You must have FFmpeg installed on your system (not just the Python library) to handle audio concatenation.

    Mac (Homebrew): brew install ffmpeg

    Linux (Debian/Ubuntu): sudo apt install ffmpeg

    Windows: Download FFmpeg and add it to your system PATH.

Installation

It is recommended to run this project in a virtual environment to manage dependencies.

    Create a Virtual Environment
    Bash

# MacOS/Linux
python3 -m venv .venv

# Windows
python -m venv .venv

Activate the Environment
Bash

# MacOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

Install Dependencies
Bash

    pip install -r requirements.txt

Usage

Run the script from your terminal by passing the path to your file:
Bash

# Convert a text file
python3 tts.py "my_document.txt"

# Convert an EPUB book
python3 tts.py "Great_Expectations.epub"

The script will:

    Read the input file (converting EPUB to text if necessary).

    Split the text into manageable 4KB chunks.

    Generate audio for each chunk asynchronously.

    Combine all audio chunks into a single file named Great_Expectations.mp3.

    Delete all temporary artifacts.

How It Works

    EPUB Parsing: If an .epub is detected, EbookLib and BeautifulSoup extract the raw text from the HTML content.

    Chunking: The text is sliced into chunks of ~4096 bytes to ensure reliability and avoid TTS API timeouts.

    TTS Generation: edge-tts communicates with the API to generate .mp3 files for every chunk.

    Concatenation: ffmpeg-python takes the list of generated audio files and stitches them into one final track.

    Cleanup: All output_chunk_*.txt and output_audio_*.mp3 files are removed, leaving only your final audiobook.

License

MIT
Suggested requirements.txt

If you haven't generated your requirements file yet, here is the correct list (specifically ensuring ffmpeg-python is used instead of ffmpeg):
Plaintext

edge-tts
ffmpeg-python
EbookLib
beautifulsoup4
