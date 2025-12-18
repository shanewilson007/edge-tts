import asyncio
import edge_tts
import ffmpeg
import glob
import sys
import re
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def epub_to_text(epub_path, output_txt_path):
    """
    Reads an epub file, extracts text from documents, and writes to a single text file.
    """
    print("Converting EPUB to text...")
    book = epub.read_epub(epub_path)

    with open(output_txt_path, "w", encoding="utf-8") as out_file:
        for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            html_content = doc.content.decode("utf-8")
            soup = BeautifulSoup(html_content, "html.parser")

            for string in soup.stripped_strings:
                out_file.write(string + "\n")
    print("EPUB conversion complete.")


def chunker(input_filename, chunk_limit):
    file_count = 1
    current_chunk_size = 0
    output_file = open(f"output_chunk_{file_count}.txt", "w", encoding="utf-8")

    with open(input_filename, "r", encoding="utf-8") as in_file:
        for line in in_file:
            if current_chunk_size + len(line) > chunk_limit and current_chunk_size > 0:
                output_file.close()
                file_count += 1
                output_file = open(
                    f"output_chunk_{file_count}.txt", "w", encoding="utf-8"
                )
                current_chunk_size = 0

            output_file.write(line)
            current_chunk_size += len(line)

    output_file.close()


def file_parser(*args):
    if args[0] == "text_files":
        regex_pattern = re.compile(r"^output_chunk_.*\.txt$")
        text_files = [
            file
            for file in glob.glob("output_chunk_*.txt")
            if regex_pattern.match(file)
        ]
        text_files.sort(key=lambda f: int(re.search(r"\d+", f).group()))
        return text_files
    elif args[0] == "mp3_files":
        regex_pattern = re.compile(r"^output_audio_.*\.mp3$")
        mp3_files = [
            file
            for file in glob.glob("output_audio_*.mp3")
            if regex_pattern.match(file)
        ]
        mp3_files.sort(key=lambda f: int(re.search(r"\d+", f).group()))
        return mp3_files


async def generate_speech(text, output_filename, voice="en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)


async def process_text_files():
    files = file_parser("text_files")
    total_files = len(files)

    for i, filename in enumerate(files, start=1):
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        output_file = f"output_audio_{i}.mp3"
        await generate_speech(content, output_file)
        remaining = total_files - i
        print(f"{output_file} generated successfully! ({remaining} remaining)")


def concat_mp3s_ffmpeg(output_file_path):
    mp3_files = file_parser("mp3_files")
    if not mp3_files:
        print("No MP3 files found to concatenate.")
        return

    input_args = []
    for file in mp3_files:
        input_args.append(ffmpeg.input(file))

    concatenated = ffmpeg.concat(*input_args, v=0, a=1)
    ffmpeg.output(concatenated, output_file_path).run(overwrite_output=True)
    print(f"Successfully combined files into: {output_file_path}")


def cleanup_temp_files():
    """Removes temporary chunk text files, audio segments, and temp converted epub."""
    patterns = ["output_chunk_*.txt", "output_audio_*.mp3", "temp_converted_epub.txt"]

    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except OSError as e:
                print(f"Error deleting {f}: {e}")

    print("Cleanup complete.")


def format_output_filename(original_filename):
    base_name = os.path.splitext(original_filename)[0]
    clean_name = re.sub(r"[^\w\d]", "_", base_name)
    clean_name = re.sub(r"_+", "_", clean_name)
    clean_name = clean_name.strip("_")

    return f"{clean_name}.mp3"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tts.py <filename.txt or filename.epub>")
        sys.exit(1)

    original_input_filename = sys.argv[1]
    processing_filename = original_input_filename

    print(f"Processing: {original_input_filename}")

    # If it is an epub, we convert it to a temp text file first.
    if original_input_filename.lower().endswith(".epub"):
        temp_text_file = "temp_converted_epub.txt"
        epub_to_text(original_input_filename, temp_text_file)
        processing_filename = temp_text_file

    # --- Step 1: Create Chunks ---
    chunker(processing_filename, 4096)

    # --- Step 2: Create Audio Segments ---
    asyncio.run(process_text_files())

    # --- Step 3: Determine Final Filename ---
    # We use the ORIGINAL filename for naming the MP3, not the temp file name
    final_output_name = format_output_filename(original_input_filename)

    # --- Step 4: Concatenate ---
    concat_mp3s_ffmpeg(final_output_name)

    # --- Step 5: Cleanup ---
    cleanup_temp_files()
