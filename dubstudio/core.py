from __future__ import annotations
import json, math, os, re, shutil, subprocess, tempfile, uuid, zipfile
from dataclasses import dataclass, asdict, field
from pathlib import Path
import numpy as np
import soundfile as sf

RATE = 48000

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args):
    p = subprocess.run([ffmpeg(), '-hide_banner', '-nostdin', '-y', *map(str, args)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=0x08000000 if os.name == 'nt' else 0)
    if p.returncode:
        raise RuntimeError(p.stderr.decode('utf-8', 'replace')[-2500:])
    return p.stderr.decode('utf-8', 'replace')


@dataclass
class Segment:
    start: float
    end: float
    transcript: str = ''
    title: str | None = None
    reference: str | None = None
    take: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    part_id: int = 0


@dataclass
class Part:
    start: float
    end: float
    id: int = 0


@dataclass
class Project:
    root: Path
    duration: float = 0
    language: str = 'pt'
    video: str = ''
    segments: list[Segment] = field(default_factory=list)
    path: str = ''
    # none: still waiting for a reference; auto: generated transcription;
    # file: imported TXT/SRT/VTT; manual: user edited the reference directly.
    reference_source: str = 'none'
    parts: list[Part] = field(default_factory=list)
    parts_confirmed: bool = False

    @property
    def audio(self):
        return self.root / 'original.wav'

    def manifest(self):
        return dict(version=1, duration=self.duration, language=self.language,
                    video=self.video, segments=[asdict(s) for s in self.segments],
                    reference_source=self.reference_source, parts=[asdict(p) for p in self.parts],
                    parts_confirmed=self.parts_confirmed)


def new_root():
    return Path(tempfile.mkdtemp(prefix='DubStudio-'))


def prepare_video(path, language, silence=.55, threshold=-35):
    """Import media and extract its audio without deciding chapter structure.

    Chapter creation is intentionally a separate user choice: manual markers, local
    transcription, or timed subtitle import.
    """
    root = new_root()
    try:
        target = root / ('video' + Path(path).suffix.lower())
        shutil.copy2(path, target)
        run_ffmpeg(['-i', target, '-map', '0:a:0', '-vn', '-ar', RATE, '-ac', 1,
                    '-c:a', 'pcm_s16le', root / 'original.wav'])
        duration = sf.info(root / 'original.wav').duration
        return Project(root, duration, language, target.name, [], '', 'none', [Part(0.0, duration, 0)], False)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


def _transcription_clip(project, start, end, temp_dir):
    start = max(0.0, float(start))
    end = min(project.duration, float(end))
    if end <= start:
        raise ValueError('Intervalo de transcrição inválido.')
    if start <= .001 and end >= project.duration - .001:
        return project.audio, 0.0
    target = Path(temp_dir) / 'part.wav'
    run_ffmpeg(['-ss', start, '-t', end - start, '-i', project.audio, '-vn',
                '-ar', RATE, '-ac', 1, '-c:a', 'pcm_s16le', target])
    return target, start


def transcribe_to_segments(project, progress=lambda _: None, model_size='small', messages=None,
                           start=0.0, end=None, part_id=0):
    """Transcribe one part and let Whisper create the initial adjustable chapters.

    The task is always ``transcribe`` (never translate), so detected speech stays in its
    original language. Returned timestamps are absolute project times.
    """
    import gc
    from faster_whisper import WhisperModel
    messages = messages or {}
    loading = messages.get('loading', 'Loading local transcription model…')
    transcribing = messages.get('transcribing', 'Transcribing audio… {pct}%')
    end = project.duration if end is None else min(project.duration, float(end))
    start = max(0.0, float(start))
    progress(loading)
    model = None
    try:
        model = WhisperModel(model_size, device='cpu', compute_type='int8')
        language = None if project.language == 'auto' else project.language
        with tempfile.TemporaryDirectory(prefix='DubStudio-part-') as td:
            source, offset = _transcription_clip(project, start, end, td)
            duration = max(.001, end - start)
            chunks, _ = model.transcribe(str(source), language=language, task='transcribe',
                word_timestamps=True, vad_filter=True, beam_size=5)
            result = []
            for chunk in chunks:
                cstart = max(start, offset + float(chunk.start))
                cend = min(end, offset + float(chunk.end))
                if cend - cstart < .05:
                    continue
                pct = min(100, int((cend - start) / duration * 100))
                progress(transcribing.format(pct=pct))
                text = (chunk.text or '').strip()
                if not text and chunk.words:
                    text = ''.join(w.word for w in chunk.words).strip()
                result.append(Segment(cstart, cend, transcript=text, reference=text or None, part_id=part_id))
            # Keep the chapters contiguous inside the part. This makes every shared border a
            # single editable decision in the UI instead of leaving tiny gaps between cues.
            for i in range(1, len(result)):
                mid = (result[i - 1].end + result[i].start) / 2
                result[i - 1].end = mid
                result[i].start = mid
            if result:
                result[0].start = start
                result[-1].end = end
            return result
    finally:
        if model is not None:
            del model
        gc.collect()


def transcribe_local(project, progress=lambda _: None, model_size='small', messages=None):
    """Offline Whisper transcription optimized for low idle memory.

    Only one model is loaded at a time and it is explicitly released when the job finishes.
    Models are downloaded on demand by faster-whisper and are not kept resident afterward.
    """
    import gc
    from faster_whisper import WhisperModel
    messages = messages or {}
    loading = messages.get('loading', 'Loading local transcription model…')
    transcribing = messages.get('transcribing', 'Transcribing audio… {pct}%')
    progress(loading)
    model = None
    try:
        model = WhisperModel(model_size, device='cpu', compute_type='int8')
        language = None if project.language == 'auto' else project.language
        chunks, _ = model.transcribe(str(project.audio), language=language, task='transcribe',
            word_timestamps=True, vad_filter=True, beam_size=5)
        if not project.segments:
            return []
        words = [[] for _ in project.segments]
        for chunk in chunks:
            pct = min(100, int(chunk.end / project.duration * 100))
            progress(transcribing.format(pct=pct))
            for word in chunk.words or []:
                mid = (word.start + word.end) / 2
                i = min(range(len(words)), key=lambda j: max(project.segments[j].start - mid,
                                                             mid - project.segments[j].end, 0))
                words[i].append(word.word)
        return [''.join(w).strip() for w in words]
    finally:
        # CTranslate2/faster-whisper can otherwise keep large allocations around until a later GC.
        if model is not None:
            del model
        gc.collect()


# Compatibility with older callers/tests.
def transcribe(project, progress=lambda _: None, model_size='small'):
    return transcribe_local(project, progress, model_size)


def peaks(path, count=2000):
    info = sf.info(path)
    step = max(1, math.ceil(info.frames / count))
    result = []
    with sf.SoundFile(path) as f:
        while True:
            block = f.read(step, dtype='float32', always_2d=True)
            if len(block) == 0:
                break
            result.append(float(np.max(np.abs(block))))
    return result


def timestamp(text):
    parts = text.replace(',', '.').split(':')
    if len(parts) not in (2, 3):
        raise ValueError('Horário de legenda inválido.')
    vals = list(map(float, parts))
    return sum(v * 60 ** i for i, v in enumerate(reversed(vals)))


def parse_reference(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('cp1252')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    suffix = Path(path).suffix.lower()
    if suffix in ('.ass', '.ssa'):
        cues = []
        for line in text.splitlines():
            if not line.lstrip().lower().startswith('dialogue:'):
                continue
            payload = line.split(':', 1)[1].lstrip()
            fields = payload.split(',', 9)
            if len(fields) < 10:
                continue
            try:
                start = timestamp(fields[1].strip())
                end = timestamp(fields[2].strip())
            except Exception:
                continue
            value = re.sub(r'\{[^}]*\}', '', fields[9]).replace('\\N', '\n').replace('\\n', '\n').strip()
            if end > start:
                cues.append((start, end, value))
        if not cues:
            raise ValueError('O arquivo não contém legendas com horários válidos.')
        return 'timed', cues
    if suffix not in ('.srt', '.vtt'):
        return 'lines', [line.strip() for line in text.splitlines() if line.strip()]
    cues = []
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if '-->' not in line:
                continue
            a, b = line.split('-->', 1)
            start = timestamp(a.strip())
            end = timestamp(b.strip().split()[0])
            if end <= start:
                raise ValueError('Legenda com fim anterior ao início.')
            value = re.sub(r'<[^>]+>', '', '\n'.join(lines[i + 1:])).strip()
            cues.append((start, end, value))
            break
    if not cues:
        raise ValueError('O arquivo não contém legendas com horários válidos.')
    return 'timed', cues


def segments_from_timed_items(items, part_start, part_end, part_id=0):
    """Create chapter segments from SRT/VTT/ASS timing, clipped to one selected part."""
    result = []
    for a, b, text in items:
        a = max(float(a), float(part_start))
        b = min(float(b), float(part_end))
        if b - a < .05:
            continue
        result.append(Segment(a, b, transcript=text, reference=text or None, part_id=part_id))
    result.sort(key=lambda s: s.start)
    # Subtitle gaps are kept: subtitles may intentionally omit silence. Adjacent chapters still
    # share a border when their cues overlap or touch closely.
    for i in range(1, len(result)):
        if result[i].start < result[i - 1].end:
            mid = (result[i].start + result[i - 1].end) / 2
            result[i - 1].end = mid
            result[i].start = mid
    return result


def match_reference(segments, kind, items):
    if kind == 'lines':
        if len(items) != len(segments):
            raise ValueError(f'O TXT tem {len(items)} linhas não vazias; o vídeo tem {len(segments)} trechos. Use uma linha por trecho ou importe SRT/VTT com horários.')
        return items
    grouped = [[] for _ in segments]
    for a, b, text in items:
        overlaps = [max(0, min(b, s.end) - max(a, s.start)) for s in segments]
        best = max(range(len(segments)), key=lambda i: overlaps[i])
        if overlaps[best] > 0:
            grouped[best].append(text)
    return ['\n'.join(g) if g else None for g in grouped]


def safe_member(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()) or '\\' in name or ':' in name:
        raise ValueError('Caminho inválido no projeto.')
    return p


def save_project(project, path):
    dest = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.dubstudio-', suffix='.tmp', dir=dest.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
            z.writestr('project.json', json.dumps(project.manifest(), ensure_ascii=False))
            names = {project.video, 'original.wav'} | {s.take for s in project.segments if s.take}
            for name in names:
                z.write(safe_member(project.root, name), name)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_project(path):
    root = new_root()
    try:
        with zipfile.ZipFile(path) as z:
            data = json.loads(z.read('project.json'))
            if data.get('version') != 1:
                raise ValueError('Versão de projeto incompatível.')
            for item in z.infolist():
                out = safe_member(root, item.filename)
                if item.is_dir():
                    out.mkdir(parents=True, exist_ok=True)
                    continue
                out.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as src, open(out, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        segments = [Segment(**s) for s in data.get('segments', [])]
        source = data.get('reference_source')
        if source not in ('none', 'auto', 'file', 'manual'):
            source = 'file' if any(s.reference is not None for s in segments) else ('auto' if any(s.transcript for s in segments) else 'none')
        if source == 'auto':
            for s in segments:
                if s.reference is None:
                    s.reference = s.transcript
        raw_parts = data.get('parts') or []
        parts = [Part(float(item['start']), float(item['end']), int(item.get('id', i))) for i, item in enumerate(raw_parts)]
        if not parts:
            parts = [Part(0.0, float(data['duration']), 0)]
        valid_ids = {part.id for part in parts}
        for seg in segments:
            if seg.part_id not in valid_ids:
                seg.part_id = parts[0].id
        confirmed = bool(data.get('parts_confirmed', bool(segments) or len(parts) > 1))
        p = Project(root, float(data['duration']), data.get('language', 'auto'), data['video'], segments,
                    str(path), source, parts, confirmed)
        if not math.isfinite(p.duration) or p.duration <= 0 or p.language not in ('auto', 'pt', 'en', 'ja'):
            raise ValueError('Projeto inválido.')
        for part in p.parts:
            if not (0 <= part.start < part.end <= p.duration + .01):
                raise ValueError('Partes do projeto inválidas.')
        for seg in p.segments:
            if not (0 <= seg.start < seg.end <= p.duration + .01):
                raise ValueError('Intervalos de projeto inválidos.')
            if seg.take and not safe_member(root, seg.take).is_file():
                raise ValueError('Gravação ausente.')
        if not safe_member(root, p.video).is_file() or not p.audio.is_file():
            raise ValueError('Mídia ausente.')
        return p
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


def render_dub(project, target):
    # Write a block at a time: long videos do not allocate a full PCM track in RAM.
    total = round(project.duration * RATE)
    cursor = 0
    # Reuse one silence block instead of allocating every second in long videos.
    silence_block = np.zeros(RATE, dtype=np.float32)

    def zeros(out, n):
        while n > 0:
            size = min(n, RATE)
            out.write(silence_block[:size])
            n -= size

    with sf.SoundFile(target, 'w', samplerate=RATE, channels=1, subtype='PCM_24') as out:
        for s in project.segments:
            start = round(s.start * RATE)
            end = min(total, round(s.end * RATE))
            zeros(out, max(0, start - cursor))
            cursor = max(cursor, start)
            if s.take:
                with sf.SoundFile(safe_member(project.root, s.take)) as take:
                    if take.samplerate != RATE:
                        raise ValueError('Taxa de amostragem da gravação inválida.')
                    remaining = end - cursor
                    while remaining > 0:
                        block = take.read(min(RATE, remaining), dtype='float32', always_2d=True)
                        if len(block) == 0:
                            break
                        out.write(block.mean(axis=1))
                        remaining -= len(block)
                        cursor += len(block)
            zeros(out, max(0, end - cursor))
            cursor = end
        zeros(out, total - cursor)


FORMATS = {
    'WAV': ('wav', ['-c:a', 'pcm_s24le']),
    'MP3': ('mp3', ['-c:a', 'libmp3lame', '-q:a', '2']),
    'FLAC': ('flac', ['-c:a', 'flac']),
    'M4A / AAC': ('m4a', ['-c:a', 'aac', '-b:a', '256k']),
    'AAC': ('aac', ['-c:a', 'aac', '-b:a', '256k']),
    'OGG / Vorbis': ('ogg', ['-c:a', 'libvorbis', '-q:a', '6']),
    'Opus': ('opus', ['-c:a', 'libopus', '-b:a', '160k']),
    'AIFF': ('aiff', ['-c:a', 'pcm_s24be']),
    'WMA': ('wma', ['-c:a', 'wmav2', '-b:a', '192k']),
    'Vídeo MP4': ('mp4', []),
    'Vídeo MKV': ('mkv', []),
}


def export_project(project, path, format_name):
    ext, codec = FORMATS[format_name]
    fd, tmp = tempfile.mkstemp(suffix='.' + ext, dir=Path(path).parent)
    os.close(fd)
    try:
        with tempfile.TemporaryDirectory(prefix='DubStudio-export-') as d:
            mix = Path(d) / 'mix.wav'
            render_dub(project, mix)
            if ext == 'wav':
                shutil.copyfile(mix, tmp)
            elif ext in ('mp4', 'mkv'):
                run_ffmpeg(['-i', project.root / project.video, '-i', mix,
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'libx264', '-preset', 'fast',
                    '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                    '-t', project.duration, *(['-movflags', '+faststart'] if ext == 'mp4' else []), tmp])
            else:
                run_ffmpeg(['-i', mix, *codec, tmp])
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
