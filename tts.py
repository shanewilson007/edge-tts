import asyncio
import edge_tts
import ffmpeg
import glob
import sys
import re
import os  # Added for file handling


def chunker(input_filename, chunk_limit):
    file_count = 1
    current_chunk_size = 0
    # Added encoding="utf-8" for safety
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

    # NOTE: I removed [:1] so it processes ALL files, not just the first one.
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

    # Using overwrite_output=True allows re-running without error
    concatenated = ffmpeg.concat(*input_args, v=0, a=1)
    ffmpeg.output(concatenated, output_file_path).run(overwrite_output=True)
    print(f"Successfully combined files into: {output_file_path}")


def cleanup_temp_files():
    """Removes temporary chunk text files and audio segments."""
    # Remove text chunks
    for f in glob.glob("output_chunk_*.txt"):
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error deleting {f}: {e}")

    # Remove audio chunks
    for f in glob.glob("output_audio_*.mp3"):
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error deleting {f}: {e}")

    print("Cleanup complete.")


def format_output_filename(original_filename):
    """
    Converts 'Legacy - Kerr, James.txt' -> 'Legacy_Kerr_James.mp3'
    """
    # 1. Remove extension (.txt)
    base_name = os.path.splitext(original_filename)[0]

    # 2. Replace non-alphanumeric chars (spaces, commas, dashes) with underscores
    clean_name = re.sub(r"[^\w\d]", "_", base_name)

    # 3. Collapse multiple underscores into one (e.g. "Legacy___Kerr" -> "Legacy_Kerr")
    clean_name = re.sub(r"_+", "_", clean_name)

    # 4. Strip leading/trailing underscores
    clean_name = clean_name.strip("_")

    return f"{clean_name}.mp3"


# --- Main Execution Flow ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tts.py <filename.txt>")
        sys.exit(1)

    input_filename = sys.argv[1]

    print(f"Processing: {input_filename}")

    # 1. Create Chunks
    chunker(input_filename, 4096)

    # 2. Create Audio Segments
    asyncio.run(process_text_files())

    # 3. Determine Final Filename
    final_output_name = format_output_filename(input_filename)

    # 4. Concatenate
    concat_mp3s_ffmpeg(final_output_name)

    # 5. Cleanup
    cleanup_temp_files()
