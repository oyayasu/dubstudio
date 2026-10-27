from __future__ import annotations
import os, shutil, sys, uuid, math, json
from pathlib import Path
import ctypes
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QSize, QRectF, QSettings, QEvent, QPoint
from PySide6.QtGui import (QColor, QPainter, QPen, QFont, QIcon, QPixmap, QAction,
                           QKeySequence, QPainterPath, QRegion)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QLineEdit, QPlainTextEdit, QTextEdit, QScrollArea, QSlider,
    QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QDialogButtonBox, QMessageBox,
    QProgressDialog, QFrame, QSizePolicy, QStackedLayout, QMenu, QKeySequenceEdit, QGroupBox, QGraphicsDropShadowEffect)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from . import core
from .recorder import Recorder
from .shortcuts import (DEFAULT_SHORTCUTS, GROUPS, LABELS, normalise,
                        find_conflict, overrides, display_label)

BUILD_VERSION = '1.2.0'


I18N = {
    'pt': {
        'open_project': 'Abrir projeto', 'close_project': 'Fechar projeto', 'import_video': 'Importar vídeo',
        'theme': 'Alternar claro / escuro', 'preferences': 'Preferências', 'restart': 'Reproduzir capítulo desde o início',
        'play_pause': 'Reproduzir / pausar capítulo · Espaço', 'pause': 'Pausar capítulo · Espaço',
        'continue_play': 'Continuar / reproduzir capítulo · Espaço', 'zoom': 'Zoom das faixas',
        'save': 'Salvar projeto · Ctrl+S', 'record': 'Gravar / parar · R', 'stop_record': 'Parar gravação · R',
        'export': 'Exportar', 'import_reference': 'Importar referência',
        'import_reference_tip': 'Importar TXT, SRT ou VTT em vez da transcrição automática',
        'reference_placeholder': 'A referência aparecerá aqui.', 'replace_reference': 'Substituir referência…',
        'use_auto': 'Usar transcrição automática', 'close_tip': 'Fechar apenas o projeto e manter o DubStudio aberto · Ctrl+W',
        'audio_language_title': 'Idioma do áudio original', 'language': 'Idioma',
        'audio_auto': 'Detectar automaticamente (mantém o idioma original)', 'audio_pt': 'Português', 'audio_en': 'English', 'audio_ja': '日本語',
        'prepare_audio': 'Preparando áudio e detectando pausas…',
        'transcribing': 'Transcrevendo áudio…', 'loading_model': 'Carregando modelo local… Na primeira vez, ele será baixado.',
        'transcribing_pct': 'Transcrevendo áudio… {pct}%',
        'transcription_failed': 'Não foi possível gerar a transcrição automática.\nVocê pode continuar usando o DubStudio e importar uma referência.',
        'prefs_title': 'Preferências', 'microphone': 'Microfone', 'default_mic': 'Microfone padrão',
        'app_language': 'Idioma do programa', 'transcription': 'Transcrição local',
        'transcription_model': 'Modelo', 'model_cost': 'Custo estimado',
        'silence_min': 'Pausa mínima¹', 'silence_threshold': 'Limite de silêncio¹',
        'prefs_note': '¹ Aplicado ao próximo vídeo importado.\nO modelo só fica na memória durante a transcrição e é descarregado ao terminar.\nUse fones ao gravar.',
        'retry_transcribe': 'Transcrever novamente',
        'model_tiny_name': 'Tiny — mais leve e mais rápido',
        'model_tiny_desc': 'RAM durante transcrição: ~0,5–1 GB • Velocidade: muito alta • Precisão: básica',
        'model_base_name': 'Base — leve e rápido',
        'model_base_desc': 'RAM durante transcrição: ~0,7–1,3 GB • Velocidade: alta • Precisão: boa em áudio limpo',
        'model_small_name': 'Small — equilibrado (recomendado)',
        'model_small_desc': 'RAM durante transcrição: ~1–2 GB • Velocidade: média • Precisão: alta para uso geral',
        'model_medium_name': 'Medium — mais preciso, mais lento',
        'model_medium_desc': 'RAM durante transcrição: ~2–4 GB • Velocidade: baixa • Precisão: muito alta',
        'model_large_name': 'Large v3 — máxima precisão, mais pesado',
        'model_large_desc': 'RAM durante transcrição: ~4–7 GB • Velocidade: muito baixa • Precisão: máxima',
        'model_estimate_note': 'Estimativas aproximadas; o uso real varia conforme o computador e o áudio.',
        'close_save_title': 'Fechar projeto', 'close_save_text': 'Salvar as alterações antes de fechar o projeto?',
        'close_save_info': 'O DubStudio continuará aberto.',
        'unsaved_discard': 'Há alterações não salvas. Descartá-las? Para salvar, escolha Não e pressione Ctrl+S.',
        'chapter': 'Capítulo', 'title': 'Título', 'exact_start': 'Início exato', 'exact_end': 'Fim exato',
        'drag_hint': 'Você também pode ajustar estes limites arrastando as agulhas diretamente na faixa.',
        'interval_error': 'O intervalo deve ficar entre os capítulos vizinhos e ter duração positiva.',
        'save_project': 'Salvar projeto', 'open_project_dialog': 'Abrir projeto', 'export_done': 'Exportação concluída.',
        'export_note': 'Exporta somente a dublagem. No vídeo, substitui o áudio original.',
        'format': 'Formato', 'exporting': 'Montando e exportando a dublagem…',
        'wait_operation': 'Aguarde a operação terminar antes de fechar.',
        'close_discard': 'Fechar e descartar alterações não salvas? Para salvar, escolha Não e pressione Ctrl+S.',
        'playback_error': 'Reprodução: {msg}', 'recording_error': 'Gravação: {msg}',
        'video_filter': 'Vídeos (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv *.mpg *.mpeg);;Todos os arquivos (*)',
        'reference_dialog': 'Importar referência', 'reference_filter': 'Referências (*.txt *.srt *.vtt)',
        'replace_take': 'Substituir a gravação do capítulo {n}?',
        'mic_error': 'Não foi possível abrir o microfone. Selecione outro dispositivo em Preferências.\n\n{msg}',
        'default_project_name': 'Projeto.dubstudio', 'missing_takes': '{n} capítulo(s) ainda sem gravação. Exportar com silêncio nesses espaços?',
        'default_export_name': 'Dublagem.{ext}',
    },
    'en': {
        'open_project': 'Open project', 'close_project': 'Close project', 'import_video': 'Import video',
        'theme': 'Toggle light / dark', 'preferences': 'Preferences', 'restart': 'Play chapter from the beginning',
        'play_pause': 'Play / pause chapter · Space', 'pause': 'Pause chapter · Space',
        'continue_play': 'Resume / play chapter · Space', 'zoom': 'Timeline zoom',
        'save': 'Save project · Ctrl+S', 'record': 'Record / stop · R', 'stop_record': 'Stop recording · R',
        'export': 'Export', 'import_reference': 'Import reference',
        'import_reference_tip': 'Import TXT, SRT or VTT instead of the automatic transcription',
        'reference_placeholder': 'The reference text will appear here.', 'replace_reference': 'Replace reference…',
        'use_auto': 'Use automatic transcription', 'close_tip': 'Close only the project and keep DubStudio open · Ctrl+W',
        'audio_language_title': 'Original audio language', 'language': 'Language',
        'audio_auto': 'Detect automatically (keeps the original language)', 'audio_pt': 'Português', 'audio_en': 'English', 'audio_ja': '日本語',
        'prepare_audio': 'Preparing audio and detecting pauses…',
        'transcribing': 'Transcribing audio…', 'loading_model': 'Loading local model… The first time, it will be downloaded.',
        'transcribing_pct': 'Transcribing audio… {pct}%',
        'transcription_failed': 'Automatic transcription could not be generated.\nYou can keep using DubStudio and import a reference.',
        'prefs_title': 'Preferences', 'microphone': 'Microphone', 'default_mic': 'Default microphone',
        'app_language': 'App language', 'transcription': 'Local transcription',
        'transcription_model': 'Model', 'model_cost': 'Estimated cost',
        'silence_min': 'Minimum pause¹', 'silence_threshold': 'Silence threshold¹',
        'prefs_note': '¹ Applied to the next imported video.\nThe model stays in memory only while transcribing and is unloaded afterward.\nUse headphones while recording.',
        'retry_transcribe': 'Transcribe again',
        'model_tiny_name': 'Tiny — lightest and fastest',
        'model_tiny_desc': 'RAM while transcribing: ~0.5–1 GB • Speed: very high • Accuracy: basic',
        'model_base_name': 'Base — light and fast',
        'model_base_desc': 'RAM while transcribing: ~0.7–1.3 GB • Speed: high • Accuracy: good on clean audio',
        'model_small_name': 'Small — balanced (recommended)',
        'model_small_desc': 'RAM while transcribing: ~1–2 GB • Speed: medium • Accuracy: high for general use',
        'model_medium_name': 'Medium — more accurate, slower',
        'model_medium_desc': 'RAM while transcribing: ~2–4 GB • Speed: low • Accuracy: very high',
        'model_large_name': 'Large v3 — maximum accuracy, heaviest',
        'model_large_desc': 'RAM while transcribing: ~4–7 GB • Speed: very low • Accuracy: maximum',
        'model_estimate_note': 'Approximate estimates; actual usage varies by computer and audio.',
        'close_save_title': 'Close project', 'close_save_text': 'Save changes before closing the project?',
        'close_save_info': 'DubStudio will remain open.',
        'unsaved_discard': 'There are unsaved changes. Discard them? To save, choose No and press Ctrl+S.',
        'chapter': 'Chapter', 'title': 'Title', 'exact_start': 'Exact start', 'exact_end': 'Exact end',
        'drag_hint': 'You can also adjust these limits by dragging the markers directly on the timeline.',
        'interval_error': 'The interval must stay between neighboring chapters and have a positive duration.',
        'save_project': 'Save project', 'open_project_dialog': 'Open project', 'export_done': 'Export complete.',
        'export_note': 'Exports only the dub. For video, it replaces the original audio.',
        'format': 'Format', 'exporting': 'Building and exporting the dub…',
        'wait_operation': 'Wait for the current operation to finish before closing.',
        'close_discard': 'Close and discard unsaved changes? To save, choose No and press Ctrl+S.',
        'playback_error': 'Playback: {msg}', 'recording_error': 'Recording: {msg}',
        'video_filter': 'Videos (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv *.mpg *.mpeg);;All files (*)',
        'reference_dialog': 'Import reference', 'reference_filter': 'References (*.txt *.srt *.vtt)',
        'replace_take': 'Replace the recording for chapter {n}?',
        'mic_error': 'Could not open the microphone. Select another device in Preferences.\n\n{msg}',
        'default_project_name': 'Project.dubstudio', 'missing_takes': '{n} chapter(s) still have no recording. Export with silence in those spaces?',
        'default_export_name': 'Dub.{ext}',
    },
    'ja': {
        'open_project': 'プロジェクトを開く', 'close_project': 'プロジェクトを閉じる', 'import_video': '動画を読み込む',
        'theme': 'ライト / ダーク切替', 'preferences': '設定', 'restart': 'チャプターの最初から再生',
        'play_pause': '再生 / 一時停止 · Space', 'pause': '一時停止 · Space',
        'continue_play': '続きから再生 · Space', 'zoom': 'タイムラインのズーム',
        'save': 'プロジェクトを保存 · Ctrl+S', 'record': '録音 / 停止 · R', 'stop_record': '録音停止 · R',
        'export': '書き出し', 'import_reference': '参照テキストを読み込む',
        'import_reference_tip': '自動文字起こしの代わりに TXT / SRT / VTT を読み込む',
        'reference_placeholder': '参照テキストがここに表示されます。', 'replace_reference': '参照テキストを置き換える…',
        'use_auto': '自動文字起こしを使う', 'close_tip': 'DubStudioを開いたままプロジェクトだけ閉じる · Ctrl+W',
        'audio_language_title': '元音声の言語', 'language': '言語',
        'audio_auto': '自動検出（元の言語のまま文字起こし）', 'audio_pt': 'Português', 'audio_en': 'English', 'audio_ja': '日本語',
        'prepare_audio': '音声を準備し、無音区間を検出しています…',
        'transcribing': '文字起こし中…', 'loading_model': 'ローカルモデルを読み込み中… 初回はダウンロードされます。',
        'transcribing_pct': '文字起こし中… {pct}%',
        'transcription_failed': '自動文字起こしを作成できませんでした。\nDubStudioはそのまま使用でき、参照テキストを読み込めます。',
        'prefs_title': '設定', 'microphone': 'マイク', 'default_mic': '既定のマイク',
        'app_language': 'アプリの言語', 'transcription': 'ローカル文字起こし',
        'transcription_model': 'モデル', 'model_cost': '推定負荷',
        'silence_min': '最小無音時間¹', 'silence_threshold': '無音しきい値¹',
        'prefs_note': '¹ 次に読み込む動画に適用されます。\nモデルは文字起こし中だけメモリに読み込まれ、終了後に解放されます。\n録音時はヘッドホンを使用してください。',
        'retry_transcribe': 'もう一度文字起こし',
        'model_tiny_name': 'Tiny — 最軽量・最速',
        'model_tiny_desc': '文字起こし中RAM: 約0.5–1 GB • 速度: 非常に速い • 精度: 基本',
        'model_base_name': 'Base — 軽量・高速',
        'model_base_desc': '文字起こし中RAM: 約0.7–1.3 GB • 速度: 速い • 精度: クリアな音声なら良好',
        'model_small_name': 'Small — バランス型（推奨）',
        'model_small_desc': '文字起こし中RAM: 約1–2 GB • 速度: 普通 • 精度: 一般用途で高い',
        'model_medium_name': 'Medium — 高精度・低速',
        'model_medium_desc': '文字起こし中RAM: 約2–4 GB • 速度: 遅い • 精度: 非常に高い',
        'model_large_name': 'Large v3 — 最高精度・最重量',
        'model_large_desc': '文字起こし中RAM: 約4–7 GB • 速度: 非常に遅い • 精度: 最高',
        'model_estimate_note': '数値は目安です。実際の使用量はPCと音声によって変わります。',
        'close_save_title': 'プロジェクトを閉じる', 'close_save_text': '閉じる前に変更を保存しますか？',
        'close_save_info': 'DubStudioは開いたままです。',
        'unsaved_discard': '未保存の変更があります。破棄しますか？ 保存する場合は「いいえ」を選び Ctrl+S を押してください。',
        'chapter': 'チャプター', 'title': 'タイトル', 'exact_start': '正確な開始', 'exact_end': '正確な終了',
        'drag_hint': 'タイムライン上のマーカーを直接ドラッグして調整することもできます。',
        'interval_error': '区間は隣接チャプターの範囲内で、正の長さである必要があります。',
        'save_project': 'プロジェクトを保存', 'open_project_dialog': 'プロジェクトを開く', 'export_done': '書き出しが完了しました。',
        'export_note': '吹き替え音声のみを書き出します。動画の場合は元の音声を置き換えます。',
        'format': '形式', 'exporting': '吹き替えを書き出しています…',
        'wait_operation': '処理が終わるまで待ってから閉じてください。',
        'close_discard': '未保存の変更を破棄して閉じますか？ 保存する場合は「いいえ」を選び Ctrl+S を押してください。',
        'playback_error': '再生: {msg}', 'recording_error': '録音: {msg}',
        'video_filter': '動画 (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv *.mpg *.mpeg);;すべてのファイル (*)',
        'reference_dialog': '参照テキストを読み込む', 'reference_filter': '参照ファイル (*.txt *.srt *.vtt)',
        'replace_take': 'チャプター {n} の録音を置き換えますか？',
        'mic_error': 'マイクを開けませんでした。設定で別のデバイスを選択してください。\n\n{msg}',
        'default_project_name': 'Project.dubstudio', 'missing_takes': 'まだ録音がないチャプターが {n} 個あります。その部分を無音で書き出しますか？',
        'default_export_name': 'Dub.{ext}',
    },
}


EXTRA_I18N = {
    'pt': {
        'prepare_audio': 'Preparando áudio…',
        'structure_title': 'Como você quer criar os capítulos desta parte?',
        'manual_chapters': 'Criar manualmente',
        'manual_chapters_tip': 'Marque um ponto A e depois um ponto B. O capítulo criado continua ajustável pelas agulhas.',
        'ai_chapters': 'Transcrever com IA local',
        'ai_chapters_tip': 'O Whisper transcreve no idioma original e cria capítulos ajustáveis automaticamente.',
        'subtitle_chapters': 'Importar legendas',
        'subtitle_chapters_tip': 'Cria capítulos usando os horários de SRT, VTT, ASS ou SSA.',
        'parts': 'Partes', 'part': 'Parte {n}', 'split_part': 'Dividir no cursor', 'merge_part': 'Unir com próxima',
        'parts_hint': 'As partes são blocos maiores do vídeo. Os números dos capítulos recomeçam dentro de cada parte.',
        'manual_start': 'Definir início no cursor', 'manual_end': 'Criar capítulo até o cursor', 'manual_cancel': 'Cancelar marcação',
        'manual_waiting': 'Escolha o início do próximo capítulo.', 'manual_next': 'Próximo início: {time}',
        'manual_bad_range': 'O fim precisa estar depois do início e dentro da parte selecionada.',
        'part_has_chapters': 'Esta parte já possui capítulos. Remova-os antes de recriar sua estrutura.',
        'parts_before_chapters': 'Divida o vídeo em partes antes de criar capítulos.',
        'no_chapters': 'Crie ou importe capítulos para começar a dublagem.',
        'subtitle_structure_dialog': 'Importar capítulos por legenda',
        'subtitle_structure_filter': 'Legendas com tempo (*.srt *.vtt *.ass *.ssa)',
        'no_timed_cues': 'Nenhuma legenda com tempo foi encontrada dentro desta parte.',
        'replace_part_chapters': 'Substituir os capítulos já existentes nesta parte?',
        'transcription_no_speech': 'A transcrição não encontrou fala suficiente para criar capítulos nesta parte.',
        'reference_placeholder': 'Texto de referência opcional para este capítulo.',
        'import_reference_tip': 'Importar texto de referência para capítulos já existentes',
        'prefs_note': 'O modelo só fica na memória durante a transcrição e é descarregado ao terminar.\nUse fones ao gravar.',
    },
    'en': {
        'prepare_audio': 'Preparing audio…',
        'structure_title': 'How do you want to create chapters for this part?',
        'manual_chapters': 'Create manually',
        'manual_chapters_tip': 'Mark point A and then point B. The created chapter remains adjustable with the handles.',
        'ai_chapters': 'Transcribe with local AI',
        'ai_chapters_tip': 'Whisper transcribes in the original language and creates adjustable chapters automatically.',
        'subtitle_chapters': 'Import subtitles',
        'subtitle_chapters_tip': 'Creates chapters from SRT, VTT, ASS or SSA timing.',
        'parts': 'Parts', 'part': 'Part {n}', 'split_part': 'Split at cursor', 'merge_part': 'Merge with next',
        'parts_hint': 'Parts are larger video blocks. Chapter numbering restarts inside each part.',
        'manual_start': 'Set start at cursor', 'manual_end': 'Create chapter to cursor', 'manual_cancel': 'Cancel mark',
        'manual_waiting': 'Choose the start of the next chapter.', 'manual_next': 'Next start: {time}',
        'manual_bad_range': 'The end must be after the start and inside the selected part.',
        'part_has_chapters': 'This part already has chapters. Remove them before rebuilding its structure.',
        'parts_before_chapters': 'Split the video into parts before creating chapters.',
        'no_chapters': 'Create or import chapters to start dubbing.',
        'subtitle_structure_dialog': 'Import chapters from subtitles',
        'subtitle_structure_filter': 'Timed subtitles (*.srt *.vtt *.ass *.ssa)',
        'no_timed_cues': 'No timed subtitle cues were found inside this part.',
        'replace_part_chapters': 'Replace the chapters already in this part?',
        'transcription_no_speech': 'The transcription did not find enough speech to create chapters in this part.',
        'reference_placeholder': 'Optional reference text for this chapter.',
        'import_reference_tip': 'Import reference text for existing chapters',
        'prefs_note': 'The model stays in memory only while transcribing and is unloaded afterward.\nUse headphones while recording.',
    },
    'ja': {
        'prepare_audio': '音声を準備しています…',
        'structure_title': 'このパートのチャプターをどう作成しますか？',
        'manual_chapters': '手動で作成',
        'manual_chapters_tip': '開始点Aと終了点Bを指定します。作成後もマーカーで調整できます。',
        'ai_chapters': 'ローカルAIで文字起こし',
        'ai_chapters_tip': 'Whisperが元の言語のまま文字起こしし、調整可能なチャプターを作成します。',
        'subtitle_chapters': '字幕を読み込む',
        'subtitle_chapters_tip': 'SRT / VTT / ASS / SSA の時間情報からチャプターを作成します。',
        'parts': 'パート', 'part': 'パート {n}', 'split_part': 'カーソル位置で分割', 'merge_part': '次のパートと結合',
        'parts_hint': 'パートは動画の大きな区切りです。チャプター番号は各パート内で1から始まります。',
        'manual_start': 'カーソル位置を開始点にする', 'manual_end': 'カーソル位置までチャプター作成', 'manual_cancel': 'マークをキャンセル',
        'manual_waiting': '次のチャプターの開始点を選んでください。', 'manual_next': '次の開始: {time}',
        'manual_bad_range': '終了点は開始点より後で、選択中のパート内である必要があります。',
        'part_has_chapters': 'このパートにはすでにチャプターがあります。構成を作り直す前に削除してください。',
        'parts_before_chapters': 'チャプターを作成する前に動画をパート分割してください。',
        'no_chapters': 'ダビングを始めるにはチャプターを作成または読み込んでください。',
        'subtitle_structure_dialog': '字幕からチャプターを読み込む',
        'subtitle_structure_filter': '時間付き字幕 (*.srt *.vtt *.ass *.ssa)',
        'no_timed_cues': 'このパート内に時間情報付き字幕が見つかりませんでした。',
        'replace_part_chapters': 'このパートの既存チャプターを置き換えますか？',
        'transcription_no_speech': 'このパートでチャプターを作成できる十分な音声が見つかりませんでした。',
        'reference_placeholder': 'このチャプターの参照テキスト（任意）',
        'import_reference_tip': '既存チャプター用の参照テキストを読み込む',
        'prefs_note': 'モデルは文字起こし中だけメモリに読み込まれ、終了後に解放されます。\n録音中はヘッドホンを使用してください。',
    },
}
for _lang, _values in EXTRA_I18N.items():
    I18N[_lang].update(_values)

LATEST_I18N = {
    'pt': {
        'import_reference': 'Importar texto de referência…',
        'import_reference_tip': 'Preenche o texto dos trechos existentes sem alterar seus cortes',
        'replace_reference': 'Substituir texto importado…',
        'reference_dialog': 'Importar texto de referência',
        'reference_filter': 'Referências (*.txt *.srt *.vtt *.ass *.ssa)',
        'import_subtitles_here': 'Criar trechos a partir de legendas…',
        'subtitle_structure_dialog': 'Criar trechos a partir de legendas',
        'no_timed_cues': 'Nenhuma legenda com tempo foi encontrada no vídeo.',
        'replace_all_chapters': 'Substituir todos os trechos existentes pelos trechos das legendas?',
        'mark_shortcut_tip': 'M sempre divide na agulha: antes das Partes, cria uma fronteira de Parte; dentro de uma Parte, cria uma fronteira de trecho.',
        'manual_chapters_tip': 'O início da Parte já é a marca 1. Posicione a agulha e pressione M; cada marca é o fim de um trecho e o começo do próximo.',
        'manual_waiting': 'O início da Parte já é a marca 1. Posicione a agulha e pressione M para dividir.',
        'split_segment_at_playhead': 'Dividir trecho na agulha',
        'undo_segment_split': 'Remover última divisão de trecho',
    },
    'en': {
        'import_reference': 'Import reference text…',
        'import_reference_tip': 'Fills text for existing segments without changing their timing',
        'replace_reference': 'Replace imported text…',
        'reference_dialog': 'Import reference text',
        'reference_filter': 'References (*.txt *.srt *.vtt *.ass *.ssa)',
        'import_subtitles_here': 'Create segments from subtitles…',
        'subtitle_structure_dialog': 'Create segments from subtitles',
        'no_timed_cues': 'No timed subtitle cues were found in the video.',
        'replace_all_chapters': 'Replace all existing segments with the subtitle segments?',
        'mark_shortcut_tip': 'M always splits at the playhead: before Parts exist it creates a Part boundary; inside a Part it creates a segment boundary.',
        'manual_chapters_tip': 'The Part start is already marker 1. Place the playhead and press M; each marker ends one segment and starts the next.',
        'manual_waiting': 'The Part start is already marker 1. Place the playhead and press M to split.',
        'split_segment_at_playhead': 'Split segment at playhead',
        'undo_segment_split': 'Remove last segment split',
    },
    'ja': {
        'import_reference': '参照テキストを読み込む…',
        'import_reference_tip': '既存区間の時間を変えずに参照テキストだけを設定します',
        'replace_reference': '読み込んだテキストを置き換える…',
        'reference_dialog': '参照テキストを読み込む',
        'reference_filter': '参照ファイル (*.txt *.srt *.vtt *.ass *.ssa)',
        'import_subtitles_here': '字幕から区間を作成…',
        'subtitle_structure_dialog': '字幕から区間を作成',
        'no_timed_cues': '動画内に時間情報付き字幕が見つかりませんでした。',
        'replace_all_chapters': '既存の区間をすべて字幕から作成した区間に置き換えますか？',
        'mark_shortcut_tip': 'Mは常に再生ヘッド位置で分割します。パート確定前はパート境界、パート内では区間境界を作ります。',
        'manual_chapters_tip': 'パート開始位置が最初からマーク1です。再生ヘッドを置いてMを押すと、その位置が前の区間の終わりと次の区間の始まりになります。',
        'manual_waiting': 'パート開始位置がマーク1です。再生ヘッドを置いてMで分割します。',
        'split_segment_at_playhead': '再生ヘッド位置で区間を分割',
        'undo_segment_split': '最後の区間分割を削除',
    },
}
for _lang, _values in LATEST_I18N.items():
    I18N[_lang].update(_values)


CLEAN_WORKFLOW_I18N = {
    'pt': {
        'divide_parts': 'Dividir em partes',
        'mark_part_end': 'Marcar divisão na agulha',
        'confirm_division': 'Confirmar divisão',
        'cancel_division': 'Cancelar divisão',
        'undo_part_marker': 'Remover última marca',
        'division_active': 'Divisão em andamento',
        'division_need_marker': 'Marque pelo menos um final de parte antes de confirmar, ou cancele para trabalhar com o vídeo inteiro.',
        'division_invalid_marker': 'Escolha um ponto diferente das bordas e das marcas já existentes.',
        'create_manual_here': 'Criar trechos manualmente',
        'transcribe_this_part': 'Transcrever esta parte com IA local',
        'import_subtitles_here': 'Criar trechos a partir de legendas…',
        'mark_segment_start': 'Marcar início na agulha',
        'create_segment_end': 'Criar trecho até a agulha',
        'cancel_manual_mode': 'Sair da criação manual',
        'edit_segment': 'Editar trecho…',
        'part_nav': 'Parte {n}/{total}',
        'previous_part': 'Parte anterior',
        'next_part': 'Próxima parte',
        'whole_video': 'Vídeo inteiro',
    },
    'en': {
        'divide_parts': 'Split into parts',
        'mark_part_end': 'Mark split at playhead',
        'confirm_division': 'Confirm split',
        'cancel_division': 'Cancel split',
        'undo_part_marker': 'Remove last marker',
        'division_active': 'Split mode active',
        'division_need_marker': 'Mark at least one part ending before confirming, or cancel to work with the whole video.',
        'division_invalid_marker': 'Choose a point away from the edges and existing markers.',
        'create_manual_here': 'Create segments manually',
        'transcribe_this_part': 'Transcribe this part with local AI',
        'import_subtitles_here': 'Create segments from subtitles…',
        'mark_segment_start': 'Mark segment start at playhead',
        'create_segment_end': 'Create segment up to here',
        'cancel_manual_mode': 'Exit manual segment creation',
        'edit_segment': 'Edit segment…',
        'part_nav': 'Part {n}/{total}',
        'previous_part': 'Previous part',
        'next_part': 'Next part',
        'whole_video': 'Whole video',
    },
    'ja': {
        'divide_parts': 'パートに分割',
        'mark_part_end': '再生ヘッド位置で分割',
        'confirm_division': '分割を確定',
        'cancel_division': '分割をキャンセル',
        'undo_part_marker': '最後のマークを削除',
        'division_active': '分割モード中',
        'division_need_marker': '確定する前に少なくとも1つ終了位置をマークするか、キャンセルして動画全体で作業してください。',
        'division_invalid_marker': '端や既存マーカーから離れた位置を選んでください。',
        'create_manual_here': '手動で区間を作成',
        'transcribe_this_part': 'このパートをローカルAIで文字起こし',
        'import_subtitles_here': '字幕から区間を作成…',
        'mark_segment_start': '再生ヘッド位置を区間開始にする',
        'create_segment_end': 'ここまでを区間にする',
        'cancel_manual_mode': '手動作成を終了',
        'edit_segment': '区間を編集…',
        'part_nav': 'パート {n}/{total}',
        'previous_part': '前のパート',
        'next_part': '次のパート',
        'whole_video': '動画全体',
    },
}
for _lang, _values in CLEAN_WORKFLOW_I18N.items():
    I18N[_lang].update(_values)

MODEL_KEYS = {
    'tiny': ('model_tiny_name', 'model_tiny_desc'),
    'base': ('model_base_name', 'model_base_desc'),
    'small': ('model_small_name', 'model_small_desc'),
    'medium': ('model_medium_name', 'model_medium_desc'),
    'large-v3': ('model_large_name', 'model_large_desc'),
}


class Job(QThread):
    result = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            def report(message):
                if self.isInterruptionRequested():
                    raise InterruptedError()
                self.progress.emit(message)
            value = self.fn(report)
            if not self.isInterruptionRequested():
                self.result.emit(value)
        except InterruptedError:
            pass
        except Exception as e:
            if not self.isInterruptionRequested():
                self.failed.emit(str(e))


# Vector icons remain crisp on Windows display scaling.
def icon(kind, color='#687080'):
    pm = QPixmap(24, 24)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if kind == 'save':
        p.drawRoundedRect(QRectF(4, 3, 16, 18), 3, 3)
        p.drawRect(QRectF(8, 3, 8, 6))
        p.drawRoundedRect(QRectF(8, 14, 8, 7), 1, 1)
    elif kind == 'export':
        p.drawLine(13, 4, 21, 4); p.drawLine(21, 4, 21, 12); p.drawLine(11, 14, 21, 4)
        p.drawLine(6, 4, 4, 4); p.drawLine(4, 4, 4, 21); p.drawLine(4, 21, 21, 21); p.drawLine(21, 21, 21, 17)
    elif kind == 'mic':
        p.drawRoundedRect(QRectF(9, 3, 6, 12), 3, 3)
        p.drawArc(QRectF(5, 8, 14, 11), 180 * 16, 180 * 16)
        p.drawLine(12, 19, 12, 22)
    elif kind == 'stop':
        p.drawRoundedRect(QRectF(6, 6, 12, 12), 2, 2)
    elif kind == 'play':
        p.drawLine(8, 5, 19, 12); p.drawLine(19, 12, 8, 19); p.drawLine(8, 19, 8, 5)
    elif kind == 'pause':
        p.drawLine(9, 5, 9, 19); p.drawLine(15, 5, 15, 19)
    elif kind == 'restart':
        p.drawArc(QRectF(4, 4, 16, 16), 35 * 16, 285 * 16)
        p.drawLine(4, 9, 4, 4); p.drawLine(4, 4, 9, 4)
        p.drawLine(10, 8, 16, 12); p.drawLine(16, 12, 10, 16); p.drawLine(10, 16, 10, 8)
    elif kind == 'folder':
        p.drawRoundedRect(QRectF(3, 7, 19, 14), 2, 2)
        p.drawLine(3, 7, 3, 4); p.drawLine(3, 4, 10, 4); p.drawLine(10, 4, 13, 7)
    elif kind == 'close_project':
        p.drawRoundedRect(QRectF(3, 5, 18, 15), 2, 2)
        p.drawLine(8, 9, 16, 17); p.drawLine(16, 9, 8, 17)
    elif kind == 'chevron_left':
        p.drawLine(15, 6, 9, 12); p.drawLine(9, 12, 15, 18)
    elif kind == 'chevron_right':
        p.drawLine(9, 6, 15, 12); p.drawLine(15, 12, 9, 18)
    elif kind == 'settings':
        for y, x in [(6, 8), (12, 16), (18, 10)]:
            p.drawLine(3, y, 21, y); p.setBrush(QColor(color)); p.drawEllipse(QRectF(x - 2, y - 2, 4, 4)); p.setBrush(Qt.NoBrush)
    elif kind == 'help':
        p.drawEllipse(QRectF(4, 4, 16, 16))
        p.drawArc(QRectF(9, 7, 7, 7), 10 * 16, 185 * 16)
        p.drawLine(12, 14, 12, 15)
        p.drawPoint(12, 18)
    elif kind == 'sun':
        p.drawEllipse(QRectF(8, 8, 8, 8))
        for a, b, c, d in [(12,2,12,4),(12,20,12,22),(2,12,4,12),(20,12,22,12),
                            (5,5,6,6),(18,18,19,19),(5,19,6,18),(18,6,19,5)]:
            p.drawLine(a, b, c, d)
    p.end()
    return QIcon(pm)


class ResizeGrip(QWidget):
    moved = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(18)
        self.setCursor(Qt.SizeVerCursor)
        self.last = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor('#9298a4'), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(self.width() // 2 - 22, 9, self.width() // 2 + 22, 9)

    def mousePressEvent(self, event):
        self.last = event.globalPosition().y()

    def mouseMoveEvent(self, event):
        if self.last is not None:
            y = event.globalPosition().y()
            self.moved.emit(int(y - self.last))
            self.last = y

    def mouseReleaseEvent(self, event):
        self.last = None


class AutoGrowTextEdit(QTextEdit):
    replaceRequested = Signal()
    autoRequested = Signal()

    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(64)
        self._min_h = 64
        self._height_update_running = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.document().documentLayout().documentSizeChanged.connect(lambda _: self.schedule_height_update())
        self.textChanged.connect(self.schedule_height_update)
        QTimer.singleShot(0, self.update_height)

    def schedule_height_update(self):
        QTimer.singleShot(0, self.update_height)

    def content_height(self):
        # QTextDocument reports its wrapped content in pixels. Force the document width to
        # follow the viewport so changing the DubStudio window immediately recalculates all
        # wrapped lines before we choose the editor height.
        viewport_w = max(40, self.viewport().width())
        self.document().setTextWidth(viewport_w)
        doc_h = float(self.document().size().height())
        frame = float(self.frameWidth() * 2)
        margins = self.contentsMargins()
        return doc_h + frame + margins.top() + margins.bottom() + 8

    def update_height(self):
        if self._height_update_running:
            return
        self._height_update_running = True
        try:
            target = max(self._min_h, int(self.content_height() + 0.999))
            if abs(self.height() - target) > 1:
                self.setFixedHeight(target)
                self.updateGeometry()
                if self.parentWidget():
                    self.parentWidget().updateGeometry()
            # There is intentionally no internal vertical scrolling. If this makes the
            # page taller than the window, the outer DubStudio page is what scrolls.
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        finally:
            self._height_update_running = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_height_update()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        replace = menu.addAction(self.property('replace_label') or 'Substituir referência…')
        replace.triggered.connect(self.replaceRequested)
        auto = menu.addAction(self.property('auto_label') or 'Usar transcrição automática')
        auto.setEnabled(bool(self.property('has_auto_reference')))
        auto.triggered.connect(self.autoRequested)
        menu.exec(event.globalPos())


class Timeline(QWidget):
    selected = Signal(int)
    edit = Signal(int)
    boundaryChanged = Signal(int, str, float)
    zoomRequested = Signal(int, float, float)
    panRequested = Signal(int)
    seekRequested = Signal(float)
    contextRequested = Signal(float, object)
    heightChanged = Signal(int)

    def __init__(self, dub=False):
        super().__init__()
        self.dub = dub
        self.project = None
        self.values = []
        self.take_peaks = {}
        self.active = 0
        self.position = 0.
        self.dark = False
        self.live = []
        self.live_seconds = 0
        self.drag_target = None
        self.dragged = False
        self.press_x = 0.
        self.scrubbing = False
        self.scrub_press_x = 0.
        self.view_start = 0.0
        self.view_end = None
        self.division_mode = False
        self.division_markers = []
        self.manual_division_mode = False
        self.vertical_resize = False
        self.resize_press_y = 0.0
        self.resize_start_height = 0
        # The whole bottom edge is the resize affordance; no tiny center-only grip.
        self.resize_margin = 16
        self.setFixedHeight(122 if not dub else 92)
        self.setMinimumWidth(700)
        self.setMouseTracking(True)
        self.seek_clicks = False

    def view_bounds(self):
        if not self.project:
            return 0.0, 1.0
        start = max(0.0, float(self.view_start or 0.0))
        end = self.project.duration if self.view_end is None else min(self.project.duration, float(self.view_end))
        if end <= start:
            return 0.0, max(.001, self.project.duration)
        return start, end

    def set_view(self, start=None, end=None):
        if not self.project:
            self.view_start, self.view_end = 0.0, None
        else:
            self.view_start = 0.0 if start is None else max(0.0, float(start))
            self.view_end = None if end is None else min(self.project.duration, float(end))
        self.update()

    def x(self, t):
        a, b = self.view_bounds()
        return 18 + (self.width() - 36) * (float(t) - a) / max(.001, b - a)

    def time_at(self, x):
        if not self.project:
            return 0.
        a, b = self.view_bounds()
        return max(a, min(b, a + (x - 18) / max(1, self.width() - 36) * (b - a)))

    @staticmethod
    def time_label(t):
        minutes = int(t // 60)
        seconds = t - minutes * 60
        return f'{minutes:02d}:{seconds:06.3f}'

    def chapter_number(self, index):
        if not self.project or index < 0 or index >= len(self.project.segments):
            return 0
        pid = self.project.segments[index].part_id
        return 1 + sum(1 for seg in self.project.segments[:index] if seg.part_id == pid)

    def visible_indices(self):
        if not self.project:
            return []
        a, b = self.view_bounds()
        return [i for i, seg in enumerate(self.project.segments) if seg.end >= a - .001 and seg.start <= b + .001]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor('#252933' if self.dark else '#ffffff')
        line = QColor('#343c4c' if self.dark else '#e5e8f1')
        top = 40 if not self.dub else 10
        h = max(54, self.height() - top - 16)
        p.setPen(QPen(line, 1)); p.setBrush(bg)
        p.drawRoundedRect(QRectF(2, top, self.width() - 4, h), 24, 24)
        if not self.project:
            return
        color = QColor('#b6a9fa' if self.dub else ('#94a4ba' if self.dark else '#8794ad'))
        view_a, view_b = self.view_bounds()

        def wave(values, start, end):
            if not values or end <= start:
                return
            p.setPen(QPen(color, 1.5))
            total = len(values)
            step = max(1, int(total / max(1, self.width() / 3)))
            span = end - start
            for j in range(0, total, step):
                t = start + span * j / max(1, total - 1)
                if t < view_a or t > view_b:
                    continue
                xx = self.x(t)
                if xx < event.rect().left() - 4 or xx > event.rect().right() + 4:
                    continue
                v = max(values[j:j + step])
                height = max(1, min(1, v) * max(10, h / 2 - 12))
                p.drawLine(int(xx), int(top + h / 2 - height), int(xx), int(top + h / 2 + height))

        if self.dub:
            for seg in self.project.segments:
                if seg.end < view_a or seg.start > view_b:
                    continue
                data = self.take_peaks.get(seg.id)
                if data:
                    wave(data[0], seg.start, min(seg.end, seg.start + data[1]))
        else:
            wave(self.values, 0, self.project.duration)
            px_per_second = max(.001, (self.width() - 36) / max(.001, view_b - view_a))
            if px_per_second >= 120: minor, major = .1, 1.0
            elif px_per_second >= 50: minor, major = .5, 1.0
            elif px_per_second >= 18: minor, major = 1.0, 5.0
            elif px_per_second >= 6: minor, major = 5.0, 10.0
            else: minor, major = 10.0, 30.0
            left_t = self.time_at(event.rect().left() - 20)
            right_t = self.time_at(event.rect().right() + 20)
            tick = math.floor(left_t / minor) * minor
            minor_pen = QColor('#667080' if self.dark else '#aeb4c0')
            major_pen = QColor('#a9afba' if self.dark else '#707785')
            while tick <= right_t + minor:
                xx = self.x(tick)
                is_major = abs((tick / major) - round(tick / major)) < 1e-5
                p.setPen(QPen(major_pen if is_major else minor_pen, 1))
                length = 9 if is_major else 5
                p.drawLine(int(xx), top + h - length - 4, int(xx), top + h - 4)
                if is_major and px_per_second >= 9:
                    p.setFont(QFont('Segoe UI', 7))
                    p.drawText(QRectF(xx - 30, top + h - 22, 60, 12), Qt.AlignCenter,
                               f'{int(tick // 60):02d}:{int(tick % 60):02d}')
                tick += minor

            if self.division_mode:
                # The beginning of the video is an implicit first mark. User-created
                # boundaries therefore start at number 2: mark 2 is simultaneously the
                # end of Part 1 and the beginning of Part 2.
                markers = [(1, 0.0, True)] + [
                    (n, t, False) for n, t in enumerate(sorted(self.division_markers), 2)
                ]
                for n, t, implicit in markers:
                    if view_a <= t <= view_b:
                        xx = self.x(t)
                        style = Qt.SolidLine if implicit else Qt.DashLine
                        p.setPen(QPen(QColor('#a991e6'), 1.5, style))
                        p.drawLine(int(xx), top - 4, int(xx), top + h)
                        p.setBrush(QColor('#a991e6')); p.setPen(Qt.NoPen)
                        p.drawEllipse(QRectF(xx - 6, top - 10, 12, 12))
                        p.setPen(QColor('#ffffff')); p.setFont(QFont('Segoe UI', 7))
                        p.drawText(QRectF(xx - 7, top - 11, 14, 14), Qt.AlignCenter, str(n))

            # Manual segment division follows exactly the same visual rule inside a Part.
            # Before the first split exists, show the Part start as implicit marker 1.
            if self.manual_division_mode and not self.division_mode:
                has_start = any(abs(seg.start - view_a) < .006 for seg in self.project.segments
                                if view_a - .001 <= seg.start <= view_b + .001)
                if not has_start:
                    xx = self.x(view_a)
                    p.setPen(QPen(QColor('#a991e6'), 1.5, Qt.SolidLine))
                    p.drawLine(int(xx), top - 4, int(xx), top + h)
                    p.setBrush(QColor('#a991e6')); p.setPen(Qt.NoPen)
                    p.drawEllipse(QRectF(xx - 6, top - 10, 12, 12))
                    p.setPen(QColor('#ffffff')); p.setFont(QFont('Segoe UI', 7))
                    p.drawText(QRectF(xx - 7, top - 11, 14, 14), Qt.AlignCenter, '1')

        visible = self.visible_indices()
        if visible:
            active_idx = self.active if self.active in visible else visible[0]
            s = self.project.segments[active_idx]
            a, b = self.x(s.start), self.x(s.end)
            p.setPen(Qt.NoPen); p.setBrush(QColor('#28b297fa'))
            p.drawRoundedRect(QRectF(a, top + 1, max(2, b - a), h - 2), 10, 10)
            if self.dub and self.live and active_idx == self.active:
                wave(self.live, s.start, min(s.end, s.start + self.live_seconds))

            for i in visible:
                seg = self.project.segments[i]
                xx = self.x(seg.start)
                prev = self.project.segments[i - 1] if i > 0 and self.project.segments[i - 1].part_id == seg.part_id else None
                shared_with_active_end = bool(prev and i - 1 == self.active and abs(prev.end - seg.start) < .006)
                active = i == self.active or shared_with_active_end
                p.setPen(QPen(QColor('#a991e6' if active else ('#555b68' if self.dark else '#c4c8d1')), 1.5 if active else 1))
                p.drawLine(int(xx), top, int(xx), top + h)
                if not self.dub:
                    if active:
                        p.setBrush(QColor('#a991e6')); p.setPen(Qt.NoPen)
                        p.drawEllipse(QRectF(xx - 11, 5, 22, 22))
                        p.setPen(QColor('#ffffff')); p.setFont(QFont('Segoe UI', 9))
                        p.drawText(QRectF(xx - 11, 5, 22, 22), Qt.AlignCenter, str(self.chapter_number(i)))
                    else:
                        p.setBrush(QColor('#323640' if self.dark else '#eef0f5')); p.setPen(Qt.NoPen)
                        p.drawEllipse(QRectF(xx - 8, 8, 16, 16))
                        p.setPen(QColor('#9299a6' if self.dark else '#7a808d')); p.setFont(QFont('Segoe UI', 7))
                        p.drawText(QRectF(xx - 8, 8, 16, 16), Qt.AlignCenter, str(self.chapter_number(i)))

            if not self.dub and self.active in visible:
                s = self.project.segments[self.active]
                start_x, end_x = self.x(s.start), self.x(s.end)
                nxt = self.project.segments[self.active + 1] if self.active + 1 < len(self.project.segments) and self.project.segments[self.active + 1].part_id == s.part_id else None
                shared_end = bool(nxt and abs(nxt.start - s.end) < .006)
                p.setPen(QPen(QColor('#a991e6'), 2)); p.setBrush(QColor('#a991e6'))
                # The numbered start badge itself is the start handle. If the next segment begins
                # exactly at the end, that next numbered badge is the shared boundary, so do not
                # paint a second end needle on top of it.
                if not shared_end:
                    p.setBrush(QColor('#f4f0ff' if not self.dark else '#373044'))
                    p.drawEllipse(QRectF(end_x - 7, 29, 14, 14))
                    p.drawLine(int(end_x), top, int(end_x), top + h)
                p.setFont(QFont('Segoe UI', 8)); p.setPen(QColor('#c8b9ee' if self.dark else '#7156b8'))
                p.drawText(QRectF(start_x - 64, 15, 128, 13), Qt.AlignCenter, self.time_label(s.start))
                p.drawText(QRectF(end_x - 64, 15, 128, 13), Qt.AlignCenter, self.time_label(s.end))

        if view_a <= self.position <= view_b:
            p.setPen(QPen(QColor('#eb7c82'), 1.5))
            xx = self.x(self.position)
            p.drawLine(int(xx), top, int(xx), top + h)

        # No visible center grip: the entire bottom edge is draggable for vertical resize.

    def index_at(self, x):
        t = self.time_at(x)
        indices = self.visible_indices()
        if not indices:
            return -1, t
        idx = min(indices, key=lambda i: max(self.project.segments[i].start - t, t - self.project.segments[i].end, 0))
        return idx, t

    def badge_at(self, pos):
        if self.dub or not self.project or pos.y() > 30:
            return None
        px = pos.x()
        candidates = [(abs(self.x(self.project.segments[i].start) - px), i) for i in self.visible_indices()]
        if not candidates:
            return None
        dist, idx = min(candidates)
        return idx if dist <= 13 else None

    def handle_at(self, pos):
        # Every numbered needle is draggable, not only the currently selected one.
        # Internal boundaries are represented by the *next* segment's start,
        # which also adjusts the preceding segment's end.
        if self.dub or not self.project or not self.project.segments:
            return None
        if pos.y() > max(46, self.height() - self.resize_margin):
            return None
        px = pos.x()
        candidates = [(abs(self.x(self.project.segments[i].start) - px), 0, i, 'start')
                      for i in self.visible_indices()]
        # The final boundary has no next numbered badge, but must still be movable.
        for i in self.visible_indices():
            seg = self.project.segments[i]
            next_is_shared = (i + 1 < len(self.project.segments) and
                              self.project.segments[i + 1].part_id == seg.part_id and
                              abs(self.project.segments[i + 1].start - seg.end) < .006)
            if not next_is_shared:
                candidates.append((abs(self.x(seg.end) - px), 1, i, 'end'))
        if not candidates:
            return None
        dist, _, i, edge = min(candidates)
        return (i, edge) if dist <= 15 else None

    def in_resize_zone(self, pos):
        return (not self.dub) and pos.y() >= self.height() - self.resize_margin

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.in_resize_zone(event.position()):
            self.vertical_resize = True
            self.resize_press_y = event.globalPosition().y()
            self.resize_start_height = self.height()
            self.setCursor(Qt.SizeVerCursor)
            return
        if not self.project:
            return
        if event.button() == Qt.RightButton and not self.dub:
            self.contextRequested.emit(self.time_at(event.position().x()), event.globalPosition().toPoint())
            return
        if event.button() != Qt.LeftButton:
            return
        handle = self.handle_at(event.position())
        if handle:
            # Click to select; keep the drag target for moving its time boundary.
            self.selected.emit(handle[0])
            self.drag_target = handle
            self.dragged = False
            self.press_x = event.position().x()
            self.setCursor(Qt.SizeHorCursor)
            self.update()
            return
        badge = self.badge_at(event.position())
        if badge is not None:
            self.selected.emit(badge)
            return
        self.scrubbing = True
        self.scrub_press_x = event.position().x()
        t = self.time_at(event.position().x())
        self.seekRequested.emit(t)
        self.setCursor(Qt.SizeHorCursor)

    def mouseMoveEvent(self, event):
        if self.vertical_resize and (event.buttons() & Qt.LeftButton):
            delta = event.globalPosition().y() - self.resize_press_y
            new_height = int(max(100, min(460, self.resize_start_height + delta)))
            if new_height != self.height():
                self.setFixedHeight(new_height)
                self.heightChanged.emit(new_height)
                self.update()
            self.setCursor(Qt.SizeVerCursor)
            return
        if not self.project:
            return
        if self.drag_target and (event.buttons() & Qt.LeftButton):
            i, edge = self.drag_target
            seg = self.project.segments[i]
            t = self.time_at(event.position().x())
            part = next((part for part in getattr(self.project, 'parts', []) if part.id == seg.part_id), None)
            part_start = part.start if part else 0.0
            part_end = part.end if part else self.project.duration
            prev = self.project.segments[i - 1] if i and self.project.segments[i - 1].part_id == seg.part_id else None
            nxt = self.project.segments[i + 1] if i + 1 < len(self.project.segments) and self.project.segments[i + 1].part_id == seg.part_id else None
            if edge == 'start':
                lower = (prev.start + .05) if prev else part_start
                upper = seg.end - .05
                value = max(lower, min(upper, t))
                if abs(value - seg.start) > .0005:
                    seg.start = value
                    if prev:
                        prev.end = value
                    self.boundaryChanged.emit(i, edge, value)
            else:
                lower = seg.start + .05
                upper = (nxt.end - .05) if nxt else part_end
                value = max(lower, min(upper, t))
                if abs(value - seg.end) > .0005:
                    seg.end = value
                    if nxt:
                        nxt.start = value
                    self.boundaryChanged.emit(i, edge, value)
            if abs(event.position().x() - self.press_x) > 3:
                self.dragged = True
            self.setToolTip(self.time_label(value))
            self.update()
            return
        if self.scrubbing and (event.buttons() & Qt.LeftButton):
            t = self.time_at(event.position().x())
            self.seekRequested.emit(t)
            self.setToolTip(self.time_label(t))
            return
        handle = self.handle_at(event.position())
        if self.in_resize_zone(event.position()):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeHorCursor if handle else Qt.ArrowCursor)
        idx, t = self.index_at(event.position().x())
        if idx < 0:
            self.setToolTip(self.time_label(t))
            return
        seg = self.project.segments[idx]
        label = seg.title if seg.title is not None else (seg.reference or seg.transcript or '')
        self.setToolTip(f'{self.chapter_number(idx)}. {label}\n{seg.start:.3f} – {seg.end:.3f} s')

    def mouseReleaseEvent(self, event):
        if self.vertical_resize:
            self.vertical_resize = False
            self.setCursor(Qt.ArrowCursor)
            self.heightChanged.emit(self.height())
            return
        if self.drag_target:
            i, _ = self.drag_target
            clicked = not self.dragged
            self.drag_target = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
            if clicked:
                self.selected.emit(i)
            return
        if self.scrubbing:
            self.scrubbing = False
            self.seekRequested.emit(self.time_at(event.position().x()))
            self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        if self.project and self.project.segments and not self.dub:
            idx = self.badge_at(event.position())
            if idx is None:
                idx = self.index_at(event.position().x())[0]
            if idx >= 0:
                self.edit.emit(idx)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if not delta:
            event.ignore()
            return
        if event.modifiers() & Qt.ControlModifier:
            self.zoomRequested.emit(delta, self.time_at(event.position().x()), event.position().x())
        else:
            self.panRequested.emit(delta)
        event.accept()


class ModernDialog(QDialog):
    """Custom rounded dialog shell with accessible close and draggable title region."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('modernDialog')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        shell = QVBoxLayout(self)
        shell.setContentsMargins(18, 18, 18, 18)
        shell.setSpacing(0)
        self.panel = QFrame(self)
        self.panel.setObjectName('dialogSurface')
        shell.addWidget(self.panel)
        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(20, 31, 60, 42))
        shadow.setOffset(0, 9)
        self.panel.setGraphicsEffect(shadow)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(22, 15, 22, 20)
        panel_layout.setSpacing(15)
        self.header = QFrame()
        self.header.setObjectName('dialogHeader')
        header_row = QHBoxLayout(self.header)
        header_row.setContentsMargins(2, 0, 0, 6)
        self.heading = QLabel()
        self.heading.setObjectName('dialogTitle')
        header_row.addWidget(self.heading)
        header_row.addStretch()
        self.dismiss = QPushButton('×')
        self.dismiss.setObjectName('dialogClose')
        self.dismiss.setToolTip('Fechar / Close')
        self.dismiss.setFixedSize(30, 30)
        self.dismiss.clicked.connect(self.reject)
        header_row.addWidget(self.dismiss)
        panel_layout.addWidget(self.header)
        self.body = QWidget(self.panel)
        self.body.setObjectName('dialogBody')
        panel_layout.addWidget(self.body, 1)
        self._drag_from = None
        self.header.installEventFilter(self)
        self.heading.installEventFilter(self)

    def setWindowTitle(self, text):
        super().setWindowTitle(text)
        if hasattr(self, 'heading'):
            self.heading.setText(text)

    def eventFilter(self, obj, event):
        if obj in (self.header, self.heading):
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.MouseMove and self._drag_from is not None and event.buttons() & Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_from)
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self._drag_from = None
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DubStudio')
        self.resize(1200, 820)
        self.setMinimumSize(760, 610)
        self.project = None
        self.index = 0
        self.dirty = False
        self.recording = None
        self.worker = None
        self.transcription_worker = None
        self.bound = None
        self.mode = 'original'
        self.pending_take = None
        self.settings = QSettings('DubStudio', 'DubStudio')
        self.shortcuts = self._load_shortcuts()
        # New appearance has its own setting: existing v1.1 dark preference does not
        # force the redesigned app to open dark on the first v1.2 launch.
        self.dark = self.settings.value('appearance/v2/dark', False, type=bool)
        self.device = None
        self.silence = .55
        self.threshold = -35.
        self.language = self.settings.value('audio_language', 'auto') or 'auto'
        if self.language not in ('auto', 'pt', 'en', 'ja'):
            self.language = 'auto'
        self.ui_language = self.settings.value('ui_language', 'pt') or 'pt'
        if self.ui_language not in I18N:
            self.ui_language = 'pt'
        self.transcription_model = self.settings.value('transcription_model', 'small') or 'small'
        if self.transcription_model not in MODEL_KEYS:
            self.transcription_model = 'small'
        self.video_ratio = 16 / 9
        self.video_area_height = 340
        self.original_timeline_height = max(100, min(460, self.settings.value('original_timeline_height', 122, type=int)))
        self.transcription_status_timer = QTimer(self)
        self.transcription_status_timer.setSingleShot(True)
        self.transcription_status_timer.timeout.connect(self.hide_transcription_status)
        self.history_timer = QTimer(self)
        self.history_timer.setSingleShot(True)
        self.history_timer.timeout.connect(self.commit_history)
        self.undo_history = []
        self.redo_history = []
        self.history_baseline = None
        self.history_suspended = False
        self.current_part_index = 0
        self.manual_start = None
        self.manual_mode = False
        self.manual_split_history = []
        self.division_mode = False
        self.division_markers = []

        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.dubplayer = QMediaPlayer(self)
        self.dubout = QAudioOutput(self)
        self.dubplayer.setAudioOutput(self.dubout)
        self.player.positionChanged.connect(self.position_changed)
        self.player.playbackStateChanged.connect(self.playback_state_changed)
        self.player.metaDataChanged.connect(self.video_metadata_changed)
        self.player.errorOccurred.connect(lambda code, msg: self.error(self.tr('playback_error', msg=msg)))
        self.dubplayer.errorOccurred.connect(lambda code, msg: self.error(self.tr('recording_error', msg=msg)))
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self.tick)

        outer = QWidget()
        outer.setObjectName('centralCanvas')
        self.setCentralWidget(outer)
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(26, 16, 26, 22)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(10)
        layout.addLayout(top)
        brand = QLabel('DubStudio')
        brand.setObjectName('brandTitle')
        top.addWidget(brand)
        top.addSpacing(14)
        self.open_btn = self.button('folder', self.tr('open_project') + ' · ' + self.shortcut_text('open'), self.open_project)
        top.addWidget(self.open_btn)
        self.close_project_btn = QPushButton(self.tr('close_project'))
        self.close_project_btn.setIcon(icon('close_project'))
        self.close_project_btn.setIconSize(QSize(20, 20))
        self.close_project_btn.setToolTip(self.tr('close_project') + ' · ' + self.shortcut_text('close'))
        self.close_project_btn.setAccessibleName(self.tr('close_project'))
        self.close_project_btn.clicked.connect(self.close_project)
        self.close_project_btn.setEnabled(False)
        top.addWidget(self.close_project_btn)
        self.import_btn = QPushButton(self.tr('import_video'))
        self.import_btn.clicked.connect(self.import_video)
        top.addWidget(self.import_btn)
        top.addStretch()
        self.help_btn = self.button('help', 'Tutorial', lambda: self.show_tutorial(True))
        top.addWidget(self.help_btn)
        self.theme_btn = self.button('sun', self.tr('theme'), self.toggle_theme)
        top.addWidget(self.theme_btn)
        self.options_btn = self.button('settings', self.tr('preferences'), self.preferences)
        top.addWidget(self.options_btn)

        self.page = QScrollArea()
        self.page.setWidgetResizable(True)
        self.page.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.page, 1)
        body = QWidget()
        self.body = body
        self.page.setWidget(body)
        stack = QVBoxLayout(body)
        stack.setContentsMargins(0, 8, 0, 12)
        stack.setSpacing(10)

        self.video_box = QFrame()
        self.video_box.setObjectName('videoBox')
        self.video_box.setFixedHeight(self.video_area_height)
        vl = QVBoxLayout(self.video_box)
        vl.setContentsMargins(18, 12, 18, 12)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()
        self.video_viewer = QFrame()
        self.video_viewer.setObjectName('videoViewer')
        self.video_viewer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        viewer_stack = QStackedLayout(self.video_viewer)
        viewer_stack.setContentsMargins(0, 0, 0, 0)
        viewer_stack.setStackingMode(QStackedLayout.StackAll)
        self.viewer_stack = viewer_stack

        self.video = QVideoWidget()
        self.video.setMinimumSize(1, 1)
        self.video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if hasattr(self.video, 'setAspectRatioMode'):
            self.video.setAspectRatioMode(Qt.KeepAspectRatio)
        self.player.setVideoOutput(self.video)
        viewer_stack.addWidget(self.video)

        self.empty = QPushButton(self.tr('import_video'))
        self.empty.setObjectName('emptyState')
        self.empty.setCursor(Qt.PointingHandCursor)
        self.empty.clicked.connect(self.import_video)
        viewer_stack.addWidget(self.empty)
        viewer_stack.setCurrentWidget(self.empty)

        row.addWidget(self.video_viewer, 0, Qt.AlignCenter)
        row.addStretch()
        vl.addStretch()
        vl.addLayout(row)
        vl.addStretch()
        self.transcription_status = QLabel('', self.video_box)
        self.transcription_status.setObjectName('transcriptionStatus')
        self.transcription_status.setAlignment(Qt.AlignCenter)
        self.transcription_status.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.transcription_status.hide()
        video_header = QLabel('VÍDEO ORIGINAL' if self.ui_language == 'pt' else ('SOURCE VIDEO' if self.ui_language == 'en' else '元の動画'))
        video_header.setObjectName('sectionHeading')
        stack.addWidget(video_header)
        self.video_header = video_header
        stack.addWidget(self.video_box)
        grip = ResizeGrip()
        grip.moved.connect(self.resize_video)
        stack.addWidget(grip)

        transport = QHBoxLayout()
        self.restart_btn = self.button('restart', self.tr('restart'), self.restart_segment)
        transport.addWidget(self.restart_btn)
        self.play_btn = self.button('play', self.tr('play_pause'), self.toggle_play)
        transport.addWidget(self.play_btn)
        self.clock = QLabel('')
        transport.addWidget(self.clock)

        # Compact part navigation. It stays hidden for a single whole-video workspace.
        self.part_nav = QWidget()
        part_nav_row = QHBoxLayout(self.part_nav)
        part_nav_row.setContentsMargins(8, 0, 0, 0)
        part_nav_row.setSpacing(4)
        self.part_prev_btn = QPushButton()
        self.part_prev_btn.setProperty('icon_kind', 'chevron_left')
        self.part_prev_btn.setIcon(icon('chevron_left'))
        self.part_prev_btn.setIconSize(QSize(18, 18))
        self.part_prev_btn.setFixedSize(30, 30)
        self.part_prev_btn.clicked.connect(self.previous_part)
        self.part_combo = QComboBox()
        self.part_combo.setFixedWidth(128)
        self.part_combo.currentIndexChanged.connect(self.part_changed)
        self.part_next_btn = QPushButton()
        self.part_next_btn.setProperty('icon_kind', 'chevron_right')
        self.part_next_btn.setIcon(icon('chevron_right'))
        self.part_next_btn.setIconSize(QSize(18, 18))
        self.part_next_btn.setFixedSize(30, 30)
        self.part_next_btn.clicked.connect(self.next_part)
        part_nav_row.addWidget(self.part_prev_btn)
        part_nav_row.addWidget(self.part_combo)
        part_nav_row.addWidget(self.part_next_btn)
        self.part_nav.hide()
        transport.addWidget(self.part_nav)

        transport.addStretch()
        self.zoom = QSlider(Qt.Horizontal)
        self.zoom.setRange(100, 3000)
        self.zoom.setValue(100)
        self.zoom.setFixedWidth(105)
        self.zoom.setToolTip(self.tr('zoom'))
        self.zoom.valueChanged.connect(self.zoom_changed)
        transport.addWidget(self.zoom)
        stack.addLayout(transport)

        self.original = Timeline()
        self.original.setFixedHeight(self.original_timeline_height)
        self.dub = Timeline(True)
        self.track_scroll = []
        for track in (self.original, self.dub):
            sc = QScrollArea()
            sc.setWidget(track)
            sc.setWidgetResizable(False)
            sc.setFrameShape(QFrame.NoFrame)
            sc.setFixedHeight(track.height() + 17)
            sc.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.track_scroll.append(sc)
            track.selected.connect(self.select)
            track.zoomRequested.connect(self.timeline_zoom_requested)
            track.panRequested.connect(self.timeline_pan_requested)
            track.heightChanged.connect(lambda h, s=sc, t=track: self.timeline_height_changed(t, s, h))
        self.original.seekRequested.connect(self.seek_to_time)
        self.original.contextRequested.connect(self.timeline_context_menu)
        self.original.edit.connect(self.edit_segment)
        self.original.boundaryChanged.connect(self.boundary_changed)
        self.original.setToolTip(self.tr('mark_shortcut_tip').replace('M', self.shortcut_text('mark')))
        original_heading = QLabel('FAIXA ORIGINAL  ·  Arraste as agulhas numeradas para ajustar os trechos')
        original_heading.setObjectName('sectionHeading')
        self.original_heading = original_heading
        stack.addWidget(original_heading)
        stack.addWidget(self.track_scroll[0])

        # Compatibility objects for older code paths. The workflow itself now lives in the
        # timeline context menu so the normal interface stays clean.
        self.structure_box = QFrame(); self.structure_box.hide()
        self.parts_hint = QLabel(self.tr('parts_hint'))
        self.structure_title = QLabel(self.tr('structure_title'))
        self.split_part_btn = QPushButton(self.tr('split_part')); self.split_part_btn.clicked.connect(self.split_part_at_cursor)
        self.merge_part_btn = QPushButton(self.tr('merge_part')); self.merge_part_btn.clicked.connect(self.merge_part_with_next)
        self.manual_btn = QPushButton(self.tr('manual_chapters')); self.manual_btn.clicked.connect(self.start_manual_chapters)
        self.ai_btn = QPushButton(self.tr('ai_chapters')); self.ai_btn.clicked.connect(self.transcribe_part_to_chapters)
        self.subtitle_btn = QPushButton(self.tr('subtitle_chapters')); self.subtitle_btn.clicked.connect(self.import_timed_chapters)
        self.manual_controls = QWidget(); self.manual_controls.hide()
        self.manual_start_btn = QPushButton(self.tr('manual_start')); self.manual_start_btn.clicked.connect(self.mark_manual_start)
        self.manual_end_btn = QPushButton(self.tr('manual_end')); self.manual_end_btn.clicked.connect(self.create_manual_chapter)
        self.manual_cancel_btn = QPushButton(self.tr('manual_cancel')); self.manual_cancel_btn.clicked.connect(self.cancel_manual_mark)
        self.manual_status = QLabel(self.tr('manual_waiting'))

        # Primary project controls sit immediately above the reference field.
        self.project_controls = QWidget()
        foot = QHBoxLayout(self.project_controls)
        foot.setContentsMargins(0, 4, 0, 4)
        self.save_btn = self.button('save', self.tr('save'), self.save_project)
        foot.addWidget(self.save_btn)
        foot.addStretch()
        self.record_btn = self.button('mic', self.tr('record'), self.record)
        self.record_btn.setObjectName('record')
        self.record_btn.setFixedSize(58, 58)
        self.record_btn.setIconSize(QSize(29, 29))
        foot.addWidget(self.record_btn)
        foot.addStretch()
        self.export_btn = self.button('export', self.tr('export'), self.export)
        foot.addWidget(self.export_btn)
        stack.addWidget(self.project_controls)

        self.ref_tools = QWidget()
        refrow = QHBoxLayout(self.ref_tools)
        refrow.setContentsMargins(0, 0, 0, 0)
        refrow.addStretch()
        self.ref_btn = QPushButton(self.tr('import_reference'))
        self.ref_btn.setToolTip(self.tr('import_reference_tip'))
        self.ref_btn.clicked.connect(self.import_reference)
        refrow.addWidget(self.ref_btn)
        refrow.addStretch()
        stack.addWidget(self.ref_tools)

        self.reference = AutoGrowTextEdit()
        self.reference.setObjectName('reference')
        self.reference.setPlaceholderText(self.tr('reference_placeholder'))
        self.reference.textChanged.connect(self.reference_changed)
        self.reference.replaceRequested.connect(self.import_reference)
        self.reference.autoRequested.connect(self.use_auto_reference)
        stack.addWidget(self.reference)
        dub_heading = QLabel('SUA GRAVAÇÃO')
        dub_heading.setObjectName('sectionHeading')
        self.dub_heading = dub_heading
        stack.addWidget(dub_heading)
        stack.addWidget(self.track_scroll[1])
        stack.addStretch()

        self.reference.hide()
        self.ref_tools.hide()
        self.structure_box.hide()
        self.manual_controls.hide()
        self.manual_mode = False
        self.manual_split_history = []
        self.original.seek_clicks = False
        self.original.manual_division_mode = False
        self.manual_start = None
        self.current_part_index = 0
        self.division_mode = False
        self.division_markers = []
        self.original.division_mode = False
        self.original.division_markers = []
        self.track_scroll[0].horizontalScrollBar().valueChanged.connect(self.track_scroll[1].horizontalScrollBar().setValue)
        self.track_scroll[1].horizontalScrollBar().valueChanged.connect(self.track_scroll[0].horizontalScrollBar().setValue)

        # Use one global dispatch path instead of competing QActions. This keeps
        # single-letter shortcuts from intercepting text typed into chapter notes.
        # All commands are resolved from the same user-editable mapping.
        QApplication.instance().installEventFilter(self)

        self.apply_language()
        self.theme()
        self.set_enabled()
        QTimer.singleShot(0, self.zoom_changed)
        QTimer.singleShot(550, self.show_tutorial)

    def tr(self, key, **kwargs):
        text = I18N.get(self.ui_language, I18N['pt']).get(key, I18N['pt'].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def apply_language(self):
        self.open_btn.setToolTip(self.tr('open_project') + ' · ' + self.shortcut_text('open'))
        self.open_btn.setAccessibleName(self.tr('open_project'))
        self.close_project_btn.setText(self.tr('close_project'))
        self.close_project_btn.setToolTip(self.tr('close_project') + ' · ' + self.shortcut_text('close'))
        self.close_project_btn.setAccessibleName(self.tr('close_project'))
        self.import_btn.setText(self.tr('import_video'))
        self.empty.setText(('＋  ' + self.tr('import_video') + '\nMP4 · MOV · MKV · WEBM'))
        self.video_header.setText({'pt': 'VÍDEO ORIGINAL', 'en': 'SOURCE VIDEO', 'ja': '元の動画'}.get(self.ui_language, 'VÍDEO ORIGINAL'))
        self.original_heading.setText({'pt': 'FAIXA ORIGINAL  ·  Arraste as agulhas numeradas para ajustar os trechos', 'en': 'SOURCE TRACK  ·  Drag numbered markers to adjust segments', 'ja': '元の音声  ·  数字付きのマーカーをドラッグして調整'}.get(self.ui_language, 'FAIXA ORIGINAL'))
        self.dub_heading.setText({'pt': 'SUA GRAVAÇÃO', 'en': 'YOUR RECORDING', 'ja': '録音'}.get(self.ui_language, 'SUA GRAVAÇÃO'))
        self.theme_btn.setToolTip(self.tr('theme'))
        self.options_btn.setToolTip(self.tr('preferences'))
        self.restart_btn.setToolTip(self.tr('restart'))
        self.play_btn.setToolTip(self.tr('play_pause').split(' · ')[0] + ' · ' + self.shortcut_text('play'))
        self.zoom.setToolTip(self.tr('zoom'))
        self.part_prev_btn.setToolTip(self.tr('previous_part'))
        self.part_next_btn.setToolTip(self.tr('next_part'))
        self.original.setToolTip(self.tr('mark_shortcut_tip').replace('M', self.shortcut_text('mark')))
        self.save_btn.setToolTip(self.tr('save').split(' · ')[0] + ' · ' + self.shortcut_text('save'))
        self.record_btn.setToolTip(self.tr('record').split(' · ')[0] + ' · ' + self.shortcut_text('record'))
        self.export_btn.setToolTip(self.tr('export'))
        self.ref_btn.setText(self.tr('import_reference'))
        self.ref_btn.setToolTip(self.tr('import_reference_tip'))
        self.reference.setPlaceholderText(self.tr('reference_placeholder'))
        self.reference.setProperty('replace_label', self.tr('replace_reference'))
        self.reference.setProperty('auto_label', self.tr('use_auto'))
        self.parts_hint.setText(self.tr('parts_hint'))
        self.structure_title.setText(self.tr('structure_title'))
        self.split_part_btn.setText(self.tr('split_part'))
        self.merge_part_btn.setText(self.tr('merge_part'))
        self.manual_btn.setText(self.tr('manual_chapters')); self.manual_btn.setToolTip(self.tr('manual_chapters_tip'))
        self.ai_btn.setText(self.tr('ai_chapters')); self.ai_btn.setToolTip(self.tr('ai_chapters_tip'))
        self.subtitle_btn.setText(self.tr('subtitle_chapters')); self.subtitle_btn.setToolTip(self.tr('subtitle_chapters_tip'))
        self.manual_start_btn.setText(self.tr('manual_start')); self.manual_end_btn.setText(self.tr('manual_end')); self.manual_cancel_btn.setText(self.tr('manual_cancel'))
        self.refresh_part_combo()

    def button(self, kind, tip, fn):
        b = QPushButton()
        b.setProperty('icon_kind', kind)
        b.setIcon(icon(kind))
        b.setIconSize(QSize(24, 24))
        b.setFixedSize(40, 38)
        b.setToolTip(tip)
        b.setAccessibleName(tip)
        b.clicked.connect(fn)
        return b

    def theme(self):
        """Quiet, native-feeling desktop palette: translucent controls and rounded panels."""
        if self.dark:
            bg, fg, surface, border = '#171b24', '#f0f2f8', '#242b37', '#3a4252'
            hover, muted, selection = '#323c4c', '#a8b4c7', '#394a69'
            raised, hint, accent = '#202632', '#8491a7', '#9da8ff'
        else:
            bg, fg, surface, border = '#f6f7fa', '#242938', '#ffffff', '#e1e5ee'
            hover, muted, selection = '#edf1f9', '#7a859a', '#e8ecff'
            raised, hint, accent = '#f0f3f9', '#74809a', '#6667d9'
        QApplication.instance().setStyleSheet(f"""
        QWidget {{ color: {fg}; font-family: 'SF Pro Text', 'Segoe UI Variable', 'Segoe UI', sans-serif; font-size: 13px; }}
        QMainWindow, QWidget#centralCanvas, QWidget#canvasBody, QScrollArea {{ background-color: {bg}; }}
        QScrollArea {{ border: none; }}
        QScrollArea > QWidget > QWidget {{ border: none; }}
        QLabel#brandTitle {{ font-weight: 700; font-size: 19px; letter-spacing: -0.4px; color: {fg}; }}
        QLabel#sectionHeading {{ color: {hint}; font-size: 11px; font-weight: 700; letter-spacing: 1px;
                                 padding-top: 7px; padding-left: 9px; padding-bottom: 1px; }}
        QPushButton {{ background-color: {surface}; color: {fg}; border: 1px solid {border};
                      border-radius: 12px; padding: 8px 14px; min-height: 22px; }}
        QPushButton:hover {{ background-color: {hover}; border-color: {muted}; }}
        QPushButton:pressed {{ background-color: {selection}; }}
        QPushButton:focus {{ border: 1px solid {accent}; }}
        QPushButton:disabled {{ color: {muted}; border-color: {border}; }}
        QPushButton#primaryButton {{ color: #ffffff; background-color: #6263d6; border: 1px solid #6263d6; }}
        QPushButton#primaryButton:hover {{ background-color: #5154c5; }}
        QPushButton#emptyState {{ background-color: {raised}; border: 2px dashed {border};
                                 border-radius: 22px; color: {hint}; font-size: 16px; font-weight: 600; }}
        QPushButton#emptyState:hover {{ color: {accent}; border-color: {accent}; background: {selection}; }}
        QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDoubleSpinBox, QKeySequenceEdit {{
            background-color: {surface}; color: {fg}; border: 1px solid {border};
            border-radius: 11px; padding: 9px 12px; selection-background-color: {selection}; min-height: 22px; }}
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus,
        QKeySequenceEdit:focus {{ border: 1px solid {accent}; }}
        QComboBox::drop-down {{ border: none; width: 26px; }}
        QGroupBox {{ border: 1px solid {border}; border-radius: 15px; margin-top: 16px;
                     padding: 16px 12px 12px 12px; background: {surface}; font-weight: 600; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                            left: 14px; padding: 0 8px; background: {surface}; }}
        QDialog {{ background-color: {bg}; }}
        QDialog#modernDialog {{ background-color: transparent; }}
        QFrame#dialogSurface {{ background-color: {surface}; border: 1px solid {border}; border-radius: 23px; }}
        QFrame#dialogHeader {{ background: transparent; border: none; }}
        QLabel#dialogTitle {{ font-size: 17px; font-weight: 700; }}
        QPushButton#dialogClose {{ background-color: {raised}; color: {hint}; border: none;
                                   font-size: 19px; border-radius: 15px; padding: 0; }}
        QPushButton#dialogClose:hover {{ background-color: {selection}; color: {fg}; }}
        QWidget#dialogBody {{ background-color: transparent; }}
        QFrame#videoBox {{ background-color: {surface}; border: 1px solid {border}; border-radius: 22px; }}
        QFrame#videoViewer {{ background: #08090c; border: none; border-radius: 20px; }}
        QLabel#transcriptionStatus {{ background: rgba(22,25,31,210); color: white;
            border: 1px solid rgba(255,255,255,30); border-radius: 12px; padding: 10px 14px; }}
        QPushButton#record {{ background: #d34d6d; color: white; border: none; border-radius: 29px; }}
        QPushButton#record:hover {{ background: #b83a5c; }}
        QScrollBar:horizontal {{ height: 8px; background: transparent; }}
        QScrollBar:vertical {{ width: 8px; background: transparent; }}
        QScrollBar::handle {{ background: {muted}; border-radius: 4px; min-width: 24px; min-height: 24px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
        QSlider::groove:horizontal {{ height: 5px; background: {border}; border-radius: 3px; }}
        QSlider::handle:horizontal {{ width: 15px; margin: -5px 0; background: {accent}; border-radius: 7px; }}
        QToolTip {{ background: {surface}; color: {fg}; border: 1px solid {border}; border-radius: 8px; padding: 7px; }}
        QMenu {{ background: {surface}; border: 1px solid {border}; border-radius: 13px; padding: 8px; }}
        QMenu::item {{ padding: 9px 22px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {selection}; }}
        """)
        for button in self.findChildren(QPushButton):
            kind = button.property('icon_kind')
            if kind:
                color = '#ffffff' if button is self.record_btn else muted
                button.setIcon(icon(kind, color))
        for track in (self.original, self.dub):
            track.dark = self.dark
            track.update()

    def show_tutorial(self, force=False):
        if not force and self.settings.value('onboarding/v2/completed', False, type=bool):
            return
        languages = {
            'pt': [
                ('Bem-vindo ao DubStudio', 'Este é seu espaço de dublagem. Importe um vídeo para começar, ou abra um projeto que você já salvou.'),
                ('Marque os trechos', 'Na faixa original, pressione M para marcar divisões. Arraste as agulhas numeradas para ajustar os limites. Dê dois cliques para editar os tempos exatos.'),
                ('Grave e compare', 'Selecione um trecho, use R para gravar e Espaço para reproduzir. Sua gravação aparece na faixa inferior.'),
                ('Seu espaço de trabalho', 'Ajuste o tamanho da faixa pela borda inferior. Use o botão de sol para o tema escuro e Preferências para personalizar seus atalhos.'),
            ],
            'en': [
                ('Welcome to DubStudio', 'This is your dubbing workspace. Import a video to begin, or open an existing project.'),
                ('Set your segments', 'Press M on the original track to split. Drag any numbered marker to adjust the boundaries. Double-click to enter exact times.'),
                ('Record and compare', 'Select a segment, press R to record and Space to play. Your take appears in the lower track.'),
                ('Make it your own', 'Drag the bottom edge of a track to resize it. Use the sun button to change theme and Preferences to remap shortcuts.'),
            ],
            'ja': [
                ('DubStudioへようこそ', '動画を読み込むか、保存したプロジェクトを開いて始めましょう。'),
                ('区間を調整', 'Mキーで区間を分割し、番号の付いたマーカーをドラッグして時間を調整します。ダブルクリックで時間を入力できます。'),
                ('録音と確認', 'Rキーで録音し、スペースキーで再生します。録音は下のトラックに表示されます。'),
                ('使いやすく調整', 'トラックの下端をドラッグして高さを変更できます。設定からショートカットも変更できます。'),
            ]
        }
        steps = languages.get(self.ui_language, languages['pt'])
        d = ModernDialog(self)
        d.setWindowTitle({'pt': 'Guia rápido', 'en': 'Quick tour', 'ja': 'クイックガイド'}.get(self.ui_language, 'Guia rápido'))
        d.resize(550, 325)
        root = QVBoxLayout(d.body)
        root.setContentsMargins(12, 10, 12, 2)
        root.setSpacing(16)
        progress = QLabel('')
        progress.setObjectName('sectionHeading')
        title = QLabel('')
        title.setStyleSheet('font-size: 21px; font-weight: 700;')
        description = QLabel('')
        description.setWordWrap(True)
        description.setMinimumHeight(82)
        root.addWidget(progress)
        root.addWidget(title)
        root.addWidget(description)
        root.addStretch()
        foot = QHBoxLayout()
        skip = QPushButton({'pt': 'Pular tutorial', 'en': 'Skip tour', 'ja': 'スキップ'}.get(self.ui_language, 'Pular'))
        previous = QPushButton({'pt': 'Voltar', 'en': 'Back', 'ja': '戻る'}.get(self.ui_language, 'Voltar'))
        next_btn = QPushButton()
        next_btn.setObjectName('primaryButton')
        foot.addWidget(skip)
        foot.addStretch()
        foot.addWidget(previous)
        foot.addWidget(next_btn)
        root.addLayout(foot)
        state = {'index': 0}
        def render():
            idx = state['index']
            progress.setText(f'{idx + 1} / {len(steps)}')
            title.setText(steps[idx][0])
            description.setText(steps[idx][1])
            previous.setEnabled(idx > 0)
            next_btn.setText(({'pt': 'Começar', 'en': 'Get started', 'ja': '開始'}.get(self.ui_language, 'Começar') if idx == len(steps) - 1
                              else {'pt': 'Próximo', 'en': 'Next', 'ja': '次へ'}.get(self.ui_language, 'Próximo')))
        def advance():
            if state['index'] == len(steps) - 1:
                d.accept()
            else:
                state['index'] += 1
                render()
        def back():
            state['index'] -= 1
            render()
        skip.clicked.connect(d.reject)
        previous.clicked.connect(back)
        next_btn.clicked.connect(advance)
        render()
        d.exec()
        # Even if skipped, do not interrupt on every launch. The help button
        # lets the user return to the tour at any time.
        self.settings.setValue('onboarding/v2/completed', True)

    def toggle_theme(self):
        self.dark = not self.dark
        self.settings.setValue('appearance/v2/dark', self.dark)
        self.theme()

    def resize_video(self, delta):
        self.video_area_height = max(160, min(900, self.video_area_height + delta))
        self.video_box.setFixedHeight(self.video_area_height)
        QTimer.singleShot(0, self.update_video_shape)

    def fit_video_size(self):
        width = max(1, self.video_box.width())
        height = max(1, self.video_box.height())
        ratio = self.video_ratio if self.video_ratio > 0 else 16 / 9
        fitted_w = width
        fitted_h = int(round(fitted_w / ratio))
        if fitted_h > height:
            fitted_h = height
            fitted_w = int(round(fitted_h * ratio))
        fitted_w = max(120, fitted_w)
        fitted_h = max(68, fitted_h)
        return fitted_w, fitted_h

    def update_video_shape(self):
        fitted_w, fitted_h = self.fit_video_size()
        self.video_viewer.setFixedSize(fitted_w, fitted_h)
        self.empty.setFixedSize(fitted_w, fitted_h)
        self.video.setFixedSize(fitted_w, fitted_h)
        radius = 20
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, fitted_w, fitted_h), radius, radius)
        polygon = path.toFillPolygon().toPolygon()
        region = QRegion(polygon)
        self.video_viewer.setMask(region)
        self.video.setMask(region)
        self.empty.setMask(region)
        if self.transcription_status.isVisible():
            size = self.transcription_status.sizeHint()
            size.setWidth(min(max(size.width(), 220), max(220, self.video_box.width() - 40)))
            x = max(10, (self.video_box.width() - size.width()) // 2)
            y = max(10, (self.video_box.height() - size.height()) // 2)
            self.transcription_status.setGeometry(x, y, size.width(), size.height())
            self.transcription_status.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'zoom'):
            self.zoom_changed()
            QTimer.singleShot(0, self.update_video_shape)

    def video_metadata_changed(self):
        try:
            meta = self.player.metaData()
            resolution = meta.value(meta.Key.Resolution) if hasattr(meta, 'Key') else None
        except Exception:
            resolution = None
        if resolution and getattr(resolution, 'width', lambda: 0)() and getattr(resolution, 'height', lambda: 0)():
            if resolution.height() > 0:
                self.video_ratio = resolution.width() / resolution.height()
        QTimer.singleShot(0, self.update_video_shape)

    def zoom_changed(self, *args):
        for t, sc in zip((self.original, self.dub), self.track_scroll):
            t.setFixedWidth(max(700, int(sc.viewport().width() * self.zoom.value() / 100)))

    def timeline_height_changed(self, track, scroll, height):
        scroll.setFixedHeight(int(height) + 17)
        if track is self.original:
            self.original_timeline_height = int(height)
            self.settings.setValue('original_timeline_height', self.original_timeline_height)

    def timeline_zoom_requested(self, delta, anchor_time, local_x):
        if not self.project:
            return
        bar = self.track_scroll[0].horizontalScrollBar()
        viewport_anchor = float(local_x) - bar.value()
        steps = delta / 120.0
        current = self.zoom.value()
        target = int(round(current * (1.18 ** steps)))
        target = max(self.zoom.minimum(), min(self.zoom.maximum(), target))
        if target == current:
            return
        self.zoom.setValue(target)
        new_x = self.original.x(anchor_time)
        bar.setValue(int(round(new_x - viewport_anchor)))

    def timeline_pan_requested(self, delta):
        if not self.project:
            return
        bar = self.track_scroll[0].horizontalScrollBar()
        amount = max(70, int(self.track_scroll[0].viewport().width() * .12))
        steps = delta / 120.0
        bar.setValue(bar.value() - int(round(steps * amount)))

    def ensure_active_visible(self):
        if not self.project or not self.project.segments or not self.track_scroll:
            return
        sc = self.track_scroll[0]
        bar = sc.horizontalScrollBar()
        s = self.project.segments[self.index]
        a, b = self.original.x(s.start), self.original.x(s.end)
        left, right = bar.value(), bar.value() + sc.viewport().width()
        margin = min(100, sc.viewport().width() // 5)
        if a < left + margin or b > right - margin:
            center = (a + b) / 2
            bar.setValue(int(round(center - sc.viewport().width() / 2)))

    def mark(self):
        self.dirty = True
        self.setWindowTitle('DubStudio •')

    def error(self, msg):
        QMessageBox.warning(self, 'DubStudio', msg)

    def ask(self, msg):
        return QMessageBox.question(self, 'DubStudio', msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

    def set_enabled(self):
        has_project = bool(self.project)
        has_chapters = bool(self.project and self.project.segments)
        rec = bool(self.recording)
        transcribing = bool(self.transcription_worker and self.transcription_worker.isRunning())
        busy = bool(self.worker)
        self.save_btn.setEnabled(has_project and not rec and not busy)
        self.export_btn.setEnabled(has_chapters and not rec and not busy)
        self.ref_btn.setEnabled(has_chapters and not rec and not busy)
        self.restart_btn.setEnabled(has_chapters and not rec and not busy)
        self.play_btn.setEnabled(has_project and not rec and not busy)
        self.zoom.setEnabled(has_project and not rec)
        self.record_btn.setEnabled(has_chapters and not rec and not busy)
        self.close_project_btn.setEnabled(has_project and not busy and not rec)
        for b in (self.open_btn, self.import_btn, self.empty):
            b.setEnabled(not busy and not rec and not transcribing)
        self.options_btn.setEnabled(not busy and not rec)
        for b in (self.manual_btn, self.ai_btn, self.subtitle_btn, self.manual_start_btn,
                  self.manual_end_btn, self.manual_cancel_btn):
            b.setEnabled(has_project and not busy and not rec and not transcribing)
        can_parts = has_project and not busy and not rec and not transcribing and not bool(self.project.segments if self.project else [])
        self.split_part_btn.setEnabled(can_parts)
        self.merge_part_btn.setEnabled(can_parts and bool(self.project and self.current_part_index < len(self.project.parts) - 1))
        self.part_combo.setEnabled(has_project and not busy and not rec)
        self.reference.setReadOnly(rec or busy)
        for t in (self.original, self.dub):
            t.setEnabled(not rec and not busy)
        self.update_part_nav()

    def job(self, label, fn, done):
        if self.worker:
            return
        self.stop_playback()
        dialog = QProgressDialog(label, '', 0, 0, self)
        dialog.setCancelButton(None)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setMinimumDuration(0)
        dialog.show()
        worker = Job(fn)
        self.worker = worker
        self.set_enabled()
        result = {}
        worker.progress.connect(dialog.setLabelText)
        worker.result.connect(lambda value: result.update(value=value))
        worker.failed.connect(lambda message: result.update(error=message))

        def finish():
            dialog.close()
            self.worker = None
            self.set_enabled()
            if 'error' in result:
                self.error(result['error'])
            elif 'value' in result:
                done(result['value'])
            worker.deleteLater()
        worker.finished.connect(finish)
        worker.start()

    def stop_transcription(self):
        if self.transcription_worker and self.transcription_worker.isRunning():
            self.transcription_worker.requestInterruption()
            if not self.transcription_worker.wait(250):
                self.transcription_worker.terminate()
                self.transcription_worker.wait(1000)
        self.transcription_worker = None
        self.hide_transcription_status()

    def reset_project(self):
        old = self.project
        self.stop_transcription()
        self.stop_playback()
        self.player.setSource(QUrl())
        self.dubplayer.setSource(QUrl())
        self.project = None
        self.index = 0
        self.dirty = False
        self.bound = None
        self.mode = 'original'
        self.pending_take = None
        self.video_ratio = 16 / 9
        self.original.project = None
        self.dub.project = None
        self.original.values = []
        self.original.position = 0.
        self.dub.position = 0.
        self.dub.take_peaks = {}
        self.dub.live = []
        self.dub.live_seconds = 0
        self.viewer_stack.setCurrentWidget(self.empty)
        self.reference.blockSignals(True)
        self.reference.clear()
        self.reference.blockSignals(False)
        self.reference.hide()
        self.ref_tools.hide()
        self.structure_box.hide()
        self.manual_controls.hide()
        self.manual_mode = False
        self.manual_split_history = []
        self.original.seek_clicks = False
        self.original.manual_division_mode = False
        self.manual_start = None
        self.current_part_index = 0
        self.division_mode = False
        self.division_markers = []
        self.original.division_mode = False
        self.original.division_markers = []
        self.original.set_view(None, None)
        self.dub.set_view(None, None)
        self.part_combo.clear()
        self.part_nav.hide()
        self.track_scroll[1].hide()
        self.clock.clear()
        self.setWindowTitle('DubStudio')
        self.reset_history()
        for track in (self.original, self.dub):
            track.update()
        self.set_enabled()
        QTimer.singleShot(0, self.update_video_shape)
        if old:
            shutil.rmtree(old.root, ignore_errors=True)

    def close_project(self):
        if not self.project or self.worker or self.recording:
            return
        if self.dirty:
            box = QMessageBox(self)
            box.setWindowTitle(self.tr('close_save_title'))
            box.setText(self.tr('close_save_text'))
            box.setInformativeText(self.tr('close_save_info'))
            box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            box.setDefaultButton(QMessageBox.Save)
            result = box.exec()
            if result == QMessageBox.Cancel:
                return
            if result == QMessageBox.Save:
                self.save_project(after=self.reset_project)
                return
        self.reset_project()

    def can_replace(self):
        if self.recording or self.worker or (self.transcription_worker and self.transcription_worker.isRunning()):
            return False
        return not self.dirty or self.ask(self.tr('unsaved_discard'))

    def import_video(self):
        if not self.can_replace():
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('import_video'), '',
            self.tr('video_filter'))
        if not path:
            return
        lang, ok = self.choose_language()
        if not ok:
            return
        self.language = lang
        self.job(self.tr('prepare_audio'),
                 lambda _: core.prepare_video(path, lang, self.silence, self.threshold), self.imported)

    def choose_language(self):
        d = ModernDialog(self)
        d.setWindowTitle(self.tr('audio_language_title'))
        f = QFormLayout(d.body)
        c = QComboBox()
        c.addItem(self.tr('audio_auto'), 'auto')
        c.addItem(self.tr('audio_pt'), 'pt')
        c.addItem(self.tr('audio_en'), 'en')
        c.addItem(self.tr('audio_ja'), 'ja')
        for i in range(c.count()):
            if c.itemData(i) == self.language:
                c.setCurrentIndex(i)
                break
        f.addRow(self.tr('language'), c)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(d.accept); bb.rejected.connect(d.reject)
        f.addRow(bb)
        accepted = d.exec() == QDialog.Accepted
        if accepted:
            self.settings.setValue('audio_language', c.currentData())
        return c.currentData(), accepted

    def imported(self, project):
        self.attach(project)
        self.mark()
        # Importing media no longer starts transcription. The structure panel deliberately
        # leaves manual creation, local AI, and subtitle timing as three equal choices.

    def attach(self, project):
        old = self.project
        self.stop_playback()
        self.player.setSource(QUrl())
        self.dubplayer.setSource(QUrl())
        if not getattr(project, 'parts', None):
            project.parts = [core.Part(0.0, project.duration, 0)]
        project.parts.sort(key=lambda p: p.start)
        project.segments.sort(key=lambda s: (s.start, s.end))
        self.project = project
        self.original.project = project
        self.dub.project = project
        self.original.values = core.peaks(project.audio)
        self.dub.take_peaks = {}
        for seg in project.segments:
            if seg.take:
                self.dub.take_peaks[seg.id] = (core.peaks(project.root / seg.take, 1000), core.sf.info(project.root / seg.take).duration)
        self.viewer_stack.setCurrentWidget(self.video)
        self.video.show()
        self.player.setSource(QUrl.fromLocalFile(str(project.root / project.video)))
        self.structure_box.hide()
        self.manual_mode = False
        self.manual_start = None
        self.manual_split_history = []
        self.division_mode = False
        self.division_markers = []
        self.original.division_mode = False
        self.original.division_markers = []
        self.original.manual_division_mode = False
        self.current_part_index = 0
        if project.segments:
            first_pid = project.segments[0].part_id
            for i, part in enumerate(project.parts):
                if part.id == first_pid:
                    self.current_part_index = i
                    break
            self.reference.show()
            self.track_scroll[1].show()
            self.select(0)
        else:
            self.reference.hide()
            self.ref_tools.hide()
            self.track_scroll[1].hide()
            self.player.setPosition(0)
            self.position_changed(0)
        self.refresh_part_combo()
        self.reset_history()
        self.update_reference_controls()
        self.update_structure_ui()
        self.set_enabled()
        QTimer.singleShot(0, self.update_video_shape)
        if old:
            shutil.rmtree(old.root, ignore_errors=True)

    def current_part(self):
        if not self.project:
            return None
        if not self.project.parts:
            self.project.parts = [core.Part(0.0, self.project.duration, 0)]
        self.current_part_index = max(0, min(self.current_part_index, len(self.project.parts) - 1))
        return self.project.parts[self.current_part_index]

    def refresh_part_combo(self):
        if not hasattr(self, 'part_combo'):
            return
        previous = self.current_part_index
        self.part_combo.blockSignals(True)
        self.part_combo.clear()
        if self.project and getattr(self.project, 'parts_confirmed', False):
            total = len(self.project.parts)
            for i, _part in enumerate(self.project.parts):
                label = self.tr('part_nav', n=i + 1, total=total) if total > 1 else self.tr('whole_video')
                self.part_combo.addItem(label, i)
            if self.part_combo.count():
                self.current_part_index = max(0, min(previous, self.part_combo.count() - 1))
                self.part_combo.setCurrentIndex(self.current_part_index)
        self.part_combo.blockSignals(False)
        self.update_part_nav()

    def update_part_nav(self):
        if not hasattr(self, 'part_nav'):
            return
        total = len(self.project.parts) if self.project and getattr(self.project, 'parts_confirmed', False) else 0
        visible = total > 1
        self.part_nav.setVisible(visible)
        if visible:
            self.part_prev_btn.setEnabled(self.current_part_index > 0 and not self.recording and not self.worker)
            self.part_next_btn.setEnabled(self.current_part_index < total - 1 and not self.recording and not self.worker)

    def set_timeline_scope(self, reset_zoom=False):
        if not self.project:
            for track in (self.original, self.dub):
                track.set_view(None, None)
            return
        if getattr(self.project, 'parts_confirmed', False) and self.project.parts:
            part = self.current_part()
            start, end = part.start, part.end
        else:
            start, end = 0.0, self.project.duration
        for track in (self.original, self.dub):
            track.set_view(start, end)
        if reset_zoom:
            self.zoom.setValue(100)
        for sc in self.track_scroll:
            sc.horizontalScrollBar().setValue(0)
        for track in (self.original, self.dub):
            track.update()

    def previous_part(self):
        if self.project and self.current_part_index > 0:
            self.part_combo.setCurrentIndex(self.current_part_index - 1)

    def next_part(self):
        if self.project and self.current_part_index + 1 < len(self.project.parts):
            self.part_combo.setCurrentIndex(self.current_part_index + 1)

    def part_changed(self, index):
        if not self.project or index < 0:
            return
        self.current_part_index = max(0, min(index, len(self.project.parts) - 1))
        self.manual_start = None
        self.manual_split_history = []
        self.manual_status.setText(self.tr('manual_waiting'))
        self.set_timeline_scope(reset_zoom=True)
        self.original.manual_division_mode = bool(self.manual_mode)
        part = self.current_part()
        if part:
            indices = [i for i, seg in enumerate(self.project.segments) if seg.part_id == part.id]
            if indices:
                self.select(indices[0])
            else:
                self.bound = None
                self.player.setPosition(round(part.start * 1000))
                self.position_changed(round(part.start * 1000))
        self.update_part_nav()
        self.set_enabled()

    def update_structure_ui(self):
        has_project = bool(self.project)
        has_chapters = bool(self.project and self.project.segments)
        # Structure actions live in the timeline's right-click menu; no permanent panel.
        self.structure_box.hide()
        self.reference.setVisible(has_chapters)
        self.track_scroll[1].setVisible(has_chapters)
        self.project_controls.setVisible(has_project)
        if not has_chapters:
            self.ref_tools.hide()
        self.refresh_part_combo()
        self.update_part_nav()
        self.set_timeline_scope(reset_zoom=False)
        self.set_enabled()

    def ensure_work_structure(self):
        if not self.project or self.division_mode:
            return False
        if not getattr(self.project, 'parts_confirmed', False):
            self.project.parts = [core.Part(0.0, self.project.duration, 0)]
            self.project.parts_confirmed = True
            self.current_part_index = 0
            self.refresh_part_combo()
            self.set_timeline_scope(reset_zoom=True)
            self.mark(); self.schedule_history()
        return True

    def begin_division(self):
        if not self.project or self.project.segments:
            return
        self.manual_mode = False
        self.manual_start = None
        self.manual_split_history = []
        self.original.manual_division_mode = False
        self.division_mode = True
        self.division_markers = []
        self.project.parts = [core.Part(0.0, self.project.duration, 0)]
        self.project.parts_confirmed = False
        self.current_part_index = 0
        self.original.division_mode = True
        self.original.division_markers = self.division_markers
        self.dub.division_mode = False
        self.set_timeline_scope(reset_zoom=True)
        self.refresh_part_combo()
        self.original.update()

    def mark_part_end(self):
        if not self.project or not self.division_mode:
            return
        # Marking is always tied to the playback needle, never to a mouse click or QAction boolean.
        t = self.player.position() / 1000.0
        if t <= .05 or t >= self.project.duration - .05 or any(abs(t - x) < .05 for x in self.division_markers):
            self.error(self.tr('division_invalid_marker'))
            return
        self.division_markers.append(t)
        self.original.division_markers = self.division_markers
        self.original.update()

    def undo_part_marker(self):
        if self.division_markers:
            self.division_markers.pop()
            self.original.division_markers = self.division_markers
            self.original.update()

    def cancel_division(self):
        if not self.project:
            return
        self.division_mode = False
        self.division_markers = []
        self.original.division_mode = False
        self.original.division_markers = []
        self.original.manual_division_mode = False
        self.project.parts = [core.Part(0.0, self.project.duration, 0)]
        self.project.parts_confirmed = False
        self.current_part_index = 0
        self.refresh_part_combo()
        self.set_timeline_scope(reset_zoom=True)
        self.original.update()

    def confirm_division(self):
        if not self.project or not self.division_mode:
            return
        if not self.division_markers:
            self.error(self.tr('division_need_marker'))
            return
        bounds = [0.0] + sorted(self.division_markers) + [self.project.duration]
        self.project.parts = [core.Part(bounds[i], bounds[i + 1], i) for i in range(len(bounds) - 1)]
        self.project.parts_confirmed = True
        self.division_mode = False
        self.division_markers = []
        self.original.division_mode = False
        self.original.division_markers = []
        self.original.manual_division_mode = False
        self.current_part_index = 0
        self.refresh_part_combo()
        self.set_timeline_scope(reset_zoom=True)
        part = self.current_part()
        if part:
            self.player.setPosition(round(part.start * 1000))
            self.position_changed(round(part.start * 1000))
        self.mark(); self.schedule_history()
        self.update_structure_ui()

    def timeline_context_menu(self, t, global_pos):
        if not self.project or self.recording or self.worker:
            return
        menu = QMenu(self)
        if self.division_mode:
            mark = menu.addAction(self.tr('mark_part_end') + '\tM')
            mark.triggered.connect(self.mark_part_end)
            if self.division_markers:
                undo = menu.addAction(self.tr('undo_part_marker'))
                undo.triggered.connect(self.undo_part_marker)
            menu.addSeparator()
            confirm = menu.addAction(self.tr('confirm_division') + '\tEnter')
            confirm.triggered.connect(self.confirm_division)
            cancel = menu.addAction(self.tr('cancel_division'))
            cancel.triggered.connect(self.cancel_division)
            menu.exec(global_pos)
            return

        if not self.project.segments and not getattr(self.project, 'parts_confirmed', False):
            divide = menu.addAction(self.tr('divide_parts'))
            divide.triggered.connect(self.begin_division)
            menu.addSeparator()

        if self.manual_mode:
            action = menu.addAction(self.tr('split_segment_at_playhead') + '\tM')
            action.triggered.connect(self.split_segment_at_playhead)
            if self.manual_split_history:
                undo = menu.addAction(self.tr('undo_segment_split') + '\tShift+M')
                undo.triggered.connect(self.undo_manual_split)
            exit_manual = menu.addAction(self.tr('cancel_manual_mode'))
            exit_manual.triggered.connect(self.stop_manual_chapters)
        else:
            manual = menu.addAction(self.tr('create_manual_here') + '\tM')
            manual.triggered.connect(self.start_manual_chapters)
            ai = menu.addAction(self.tr('transcribe_this_part'))
            ai.triggered.connect(self.transcribe_part_to_chapters)
            subs = menu.addAction(self.tr('import_subtitles_here'))
            subs.triggered.connect(self.import_timed_chapters)

        part = self.current_part()
        if part:
            candidates = [i for i, seg in enumerate(self.project.segments)
                          if seg.part_id == part.id and seg.start <= t <= seg.end]
            if candidates:
                idx = candidates[0]
                menu.addSeparator()
                edit = menu.addAction(self.tr('edit_segment'))
                edit.triggered.connect(lambda _=False, i=idx: self.edit_segment(i))
        menu.exec(global_pos)

    # Legacy hidden controls call these wrappers; normal use is through the context menu.
    def split_part_at_cursor(self):
        if not self.division_mode:
            self.begin_division()
        self.mark_part_end()

    def merge_part_with_next(self):
        if not self.project or self.project.segments:
            return
        i = self.current_part_index
        if i < 0 or i + 1 >= len(self.project.parts):
            return
        self.project.parts[i].end = self.project.parts[i + 1].end
        del self.project.parts[i + 1]
        self.project.parts_confirmed = len(self.project.parts) > 1
        self.refresh_part_combo(); self.set_timeline_scope(reset_zoom=True)
        self.mark(); self.schedule_history()

    def start_manual_chapters(self):
        if not self.ensure_work_structure():
            return
        self.manual_mode = True
        self.manual_start = None
        self.manual_split_history = []
        self.original.seek_clicks = False
        self.original.manual_division_mode = True
        self.manual_controls.hide()
        self.manual_status.setText(self.tr('manual_waiting'))
        self.original.update()

    def stop_manual_chapters(self):
        self.manual_mode = False
        self.manual_start = None
        self.manual_split_history = []
        self.original.manual_division_mode = False
        self.manual_status.setText(self.tr('manual_waiting'))
        self.original.update()

    def cancel_manual_mark(self):
        # Kept for compatibility with the old hidden controls. There is no A/B pair
        # anymore: a manual mark is always an immediate split at the playhead.
        self.undo_manual_split()

    def split_segment_at_playhead(self):
        if not self.ensure_work_structure():
            return
        part = self.current_part()
        if not part:
            return
        # Same rule as Part division: M/context-menu actions always use the needle.
        value = self.player.position() / 1000.0
        value = max(part.start, min(part.end, value))
        if value <= part.start + .05 or value >= part.end - .05:
            self.error(self.tr('division_invalid_marker'))
            return

        part_segments = sorted(
            [seg for seg in self.project.segments if seg.part_id == part.id],
            key=lambda seg: (seg.start, seg.end)
        )
        created_base = False
        if not part_segments:
            # The Part itself is the initial segment. Its start is implicit marker 1;
            # the first M splits it into segment 1 and segment 2.
            base = core.Segment(part.start, part.end, part_id=part.id)
            self.project.segments.append(base)
            part_segments = [base]
            created_base = True

        target = next((seg for seg in part_segments
                       if seg.start + .05 < value < seg.end - .05), None)
        if target is None:
            if created_base:
                self.project.segments.remove(part_segments[0])
            self.error(self.tr('division_invalid_marker'))
            return

        original_end = target.end
        right = core.Segment(value, original_end, part_id=part.id)
        target.end = value
        self.project.segments.append(right)
        self.project.segments.sort(key=lambda seg: (seg.start, seg.end))
        self.manual_split_history.append({
            'part_id': part.id,
            'left_id': target.id,
            'right_id': right.id,
            'original_end': original_end,
            'created_base': created_base,
        })

        self.reference.show(); self.track_scroll[1].show()
        self.update_structure_ui(); self.update_reference_controls()
        self.original.manual_division_mode = True
        idx = self.project.segments.index(right)
        self.select(idx)
        # select() seeks to the newly-created shared boundary, which is exactly where
        # the user's playhead was when M was pressed.
        self.player.setPosition(round(value * 1000))
        self.position_changed(round(value * 1000))
        self.mark(); self.schedule_history()
        for track in (self.original, self.dub):
            track.update()

    def undo_manual_split(self):
        if not self.project or not self.manual_mode or not self.manual_split_history:
            return
        info = self.manual_split_history.pop()
        left = next((seg for seg in self.project.segments if seg.id == info['left_id']), None)
        right = next((seg for seg in self.project.segments if seg.id == info['right_id']), None)
        if not left or not right:
            return
        boundary = right.start
        if info.get('created_base'):
            # Undoing the very first M restores the pristine Part with no segments.
            self.project.segments = [seg for seg in self.project.segments
                                     if seg.id not in (left.id, right.id)]
            self.bound = None
            self.reference.hide(); self.track_scroll[1].hide(); self.ref_tools.hide()
            self.player.setPosition(round(self.current_part().start * 1000))
            self.position_changed(round(self.current_part().start * 1000))
        else:
            left.end = float(info['original_end'])
            self.project.segments = [seg for seg in self.project.segments if seg.id != right.id]
            self.project.segments.sort(key=lambda seg: (seg.start, seg.end))
            idx = self.project.segments.index(left)
            self.select(idx)
            self.player.setPosition(round(boundary * 1000))
            self.position_changed(round(boundary * 1000))
        self.update_structure_ui(); self.update_reference_controls()
        self.original.manual_division_mode = True
        self.mark(); self.schedule_history()
        for track in (self.original, self.dub):
            track.update()

    # Compatibility wrappers for the old hidden A/B controls.
    def mark_manual_start(self, t=None):
        self.split_segment_at_playhead()

    def create_manual_chapter(self, end_time=None):
        self.split_segment_at_playhead()

    def _replace_part_segments(self, part, new_segments):
        old = [s for s in self.project.segments if s.part_id == part.id]
        if old and not self.ask(self.tr('replace_part_chapters')):
            return False
        self.project.segments = [s for s in self.project.segments if s.part_id != part.id] + list(new_segments)
        self.project.segments.sort(key=lambda s: (s.start, s.end))
        self.dub.take_peaks = {sid: data for sid, data in self.dub.take_peaks.items() if any(seg.id == sid for seg in self.project.segments)}
        self.update_structure_ui(); self.update_reference_controls()
        return True

    def transcribe_part_to_chapters(self):
        if not self.project or (self.transcription_worker and self.transcription_worker.isRunning()):
            return
        if not self.ensure_work_structure():
            return
        self.manual_mode = False; self.manual_split_history = []; self.original.seek_clicks = False; self.original.manual_division_mode = False; self.manual_controls.hide()
        part = self.current_part()
        if not part:
            return
        project = self.project
        self.show_transcription_status(self.tr('transcribing'))
        messages = {'loading': self.tr('loading_model'), 'transcribing': self.tr('transcribing_pct', pct='{pct}')}
        worker = Job(lambda progress: core.transcribe_to_segments(project, progress, self.transcription_model, messages,
                                                                  part.start, part.end, part.id))
        self.transcription_worker = worker
        result = {}
        worker.progress.connect(lambda text: self.show_transcription_status(text))
        worker.result.connect(lambda value: result.update(value=value))
        worker.failed.connect(lambda message: result.update(error=message))
        def finish():
            if self.project is project:
                if 'value' in result:
                    segments = result['value']
                    if not segments:
                        self.show_transcription_status(self.tr('transcription_no_speech'), True)
                    elif self._replace_part_segments(part, segments):
                        self.project.reference_source = 'auto'
                        idx = self.project.segments.index(segments[0])
                        self.select(idx); self.mark(); self.schedule_history(); self.hide_transcription_status()
                elif 'error' in result:
                    self.show_transcription_status(str(result['error']), True)
            self.transcription_worker = None
            self.set_enabled(); worker.deleteLater()
        worker.finished.connect(finish)
        self.set_enabled(); worker.start()

    def import_timed_chapters(self):
        """Import one timed subtitle file for the whole video and distribute it into Parts.

        The subtitle file may cover the entire source video. Each cue is clipped to any Part
        it overlaps, so the user imports once instead of repeating the same file per Part.
        """
        if not self.project:
            return
        if not self.ensure_work_structure():
            return
        self.manual_mode = False; self.manual_split_history = []; self.original.seek_clicks = False; self.original.manual_division_mode = False; self.manual_controls.hide()
        path, _ = QFileDialog.getOpenFileName(self, self.tr('subtitle_structure_dialog'), '', self.tr('subtitle_structure_filter'))
        if not path:
            return
        try:
            kind, items = core.parse_reference(path)
            if kind != 'timed':
                raise ValueError(self.tr('no_timed_cues'))
            segments = []
            for part in self.project.parts:
                segments.extend(core.segments_from_timed_items(items, part.start, part.end, part.id))
            segments.sort(key=lambda s: (s.start, s.end))
            if not segments:
                raise ValueError(self.tr('no_timed_cues'))
            if self.project.segments and not self.ask(self.tr('replace_all_chapters')):
                return
            self.project.segments = segments
            self.dub.take_peaks = {}
            self.project.reference_source = 'file'
            self.update_structure_ui(); self.update_reference_controls()
            # Stay in the Part the user was working on when possible.
            part = self.current_part()
            indices = [i for i, seg in enumerate(self.project.segments) if not part or seg.part_id == part.id]
            self.select(indices[0] if indices else 0)
            self.ref_tools.hide()
            self.mark(); self.schedule_history()
        except Exception as e:
            self.error(str(e))

    def seek_to_time(self, t):
        if not self.project:
            return
        self.bound = None
        low, high = 0.0, self.project.duration
        if getattr(self.project, 'parts_confirmed', False):
            part = self.current_part()
            if part:
                low, high = part.start, part.end
        self.player.setPosition(round(max(low, min(high, t)) * 1000))

    def show_transcription_status(self, text, error=False):
        self.transcription_status_timer.stop()
        self.transcription_status.setText(text)
        self.transcription_status.setToolTip(text if error else '')
        self.transcription_status.adjustSize()
        self.transcription_status.show()
        # Status messages are toasts, never permanent overlays. The background job keeps
        # running after the toast fades; later progress may briefly show a fresh toast.
        self.transcription_status_timer.start(6500 if error else 4200)
        QTimer.singleShot(0, self.update_video_shape)

    def hide_transcription_status(self):
        self.transcription_status_timer.stop()
        self.transcription_status.hide()

    def transcribe(self):
        if not self.project or (self.transcription_worker and self.transcription_worker.isRunning()):
            return
        project = self.project
        self.show_transcription_status(self.tr('transcribing'))
        messages = {
            'loading': self.tr('loading_model'),
            'transcribing': self.tr('transcribing_pct', pct='{pct}'),
        }
        fn = lambda progress: core.transcribe_local(project, progress, self.transcription_model, messages)
        worker = Job(fn)
        self.transcription_worker = worker
        result = {}
        worker.progress.connect(lambda text: self.show_transcription_status(text))
        worker.result.connect(lambda value: result.update(value=value))
        worker.failed.connect(lambda message: result.update(error=message))

        def finish():
            if self.project is project:
                if 'value' in result:
                    texts = result['value']
                    for s, text in zip(project.segments, texts):
                        s.transcript = text
                    # An imported/manual reference always wins. Otherwise the native transcription
                    # becomes the reference itself, exactly as if a file had been imported.
                    if project.reference_source == 'none':
                        for s, text in zip(project.segments, texts):
                            s.reference = text
                        project.reference_source = 'auto'
                    elif project.reference_source in ('manual', 'file'):
                        # Preserve anything the user supplied, but let native transcription
                        # fill chapters that still have no reference text.
                        for s, text in zip(project.segments, texts):
                            if s.reference is None:
                                s.reference = text
                    self.select(self.index)
                    if project.reference_source == 'auto':
                        self.reset_history()
                    self.mark()
                    self.hide_transcription_status()
                elif 'error' in result:
                    self.show_transcription_status(self.tr('transcription_failed'), True)
                self.update_reference_controls()
            self.transcription_worker = None
            self.set_enabled()
            worker.deleteLater()
        worker.finished.connect(finish)
        self.set_enabled()
        worker.start()

    def update_reference_controls(self):
        if not self.project or not self.project.segments:
            self.ref_tools.hide()
            return
        visible = bool(self.project.reference_source == 'none')
        self.ref_tools.setVisible(visible)
        self.reference.setProperty('has_auto_reference', bool(self.project and any(s.transcript for s in self.project.segments)))

    def select(self, i):
        if self.recording or not self.project or not self.project.segments:
            return
        self.stop_playback()
        self.index = max(0, min(i, len(self.project.segments) - 1))
        s = self.project.segments[self.index]
        previous_part_index = self.current_part_index
        for pi, part in enumerate(self.project.parts):
            if part.id == s.part_id:
                self.current_part_index = pi
                if self.part_combo.currentIndex() != pi:
                    self.part_combo.blockSignals(True); self.part_combo.setCurrentIndex(pi); self.part_combo.blockSignals(False)
                break
        if self.current_part_index != previous_part_index:
            self.set_timeline_scope(reset_zoom=True)
            self.update_part_nav()
        self.original.active = self.dub.active = self.index
        self.reference.blockSignals(True)
        self.reference.setPlainText(s.reference if s.reference is not None else s.transcript)
        self.reference.blockSignals(False)
        self.reference.update_height()
        self.player.setPosition(round(s.start * 1000))
        self.position_changed(round(s.start * 1000))
        for t in (self.original, self.dub):
            t.update()
        QTimer.singleShot(0, self.ensure_active_visible)

    def reference_changed(self):
        if self.project and not self.recording:
            self.project.segments[self.index].reference = self.reference.toPlainText()
            if self.project.reference_source in ('none', 'auto'):
                self.project.reference_source = 'manual'
            self.update_reference_controls()
            self.mark()
            if not self.history_suspended:
                self.schedule_history(450)

    def use_auto_reference(self):
        if not self.project:
            return
        if not any(s.transcript for s in self.project.segments):
            self.project.reference_source = 'none'
            self.update_reference_controls()
            self.transcribe()
            return
        for s in self.project.segments:
            s.reference = s.transcript
        self.project.reference_source = 'auto'
        self.select(self.index)
        self.update_reference_controls()
        self.mark()
        self.schedule_history()

    def import_reference(self):
        if not self.project:
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('reference_dialog'), '', self.tr('reference_filter'))
        if not path:
            return
        try:
            kind, items = core.parse_reference(path)
            values = core.match_reference(self.project.segments, kind, items)
            for s, value in zip(self.project.segments, values):
                s.reference = value
            self.project.reference_source = 'file'
            self.ref_tools.hide()
            self.select(self.index)
            self.update_reference_controls()
            self.mark()
            self.schedule_history()
        except Exception as e:
            self.error(str(e))

    def boundary_changed(self, i, edge, value):
        self.original.active = self.dub.active = i
        self.index = i
        seg = self.project.segments[i]
        self.mark()
        self.schedule_history(300)
        if self.player.playbackState() != QMediaPlayer.PlayingState:
            self.player.setPosition(round(seg.start * 1000))
        for t in (self.original, self.dub):
            t.update()

    def edit_segment(self, i):
        if not self.project or not self.project.segments or self.recording or self.worker:
            return
        self.select(i)
        seg = self.project.segments[i]
        chapter_no = self.original.chapter_number(i)
        d = ModernDialog(self)
        d.setWindowTitle(f"{self.tr('chapter')} {chapter_no}")
        d.setSizeGripEnabled(True)
        d.setMinimumSize(430, 210)
        d.resize(500, 250)
        f = QFormLayout(d.body)
        f.addRow(self.tr('chapter'), QLabel(str(chapter_no)))
        start = QDoubleSpinBox(); end = QDoubleSpinBox()
        for box in (start, end):
            box.setDecimals(3); box.setRange(0, self.project.duration); box.setSuffix(' s'); box.setSingleStep(.01)
        start.setValue(seg.start); end.setValue(seg.end)
        f.addRow(self.tr('exact_start'), start); f.addRow(self.tr('exact_end'), end)
        note = QLabel(self.tr('drag_hint')); note.setWordWrap(True); f.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(d.accept); bb.rejected.connect(d.reject); f.addRow(bb)
        if d.exec() != QDialog.Accepted:
            return
        part = next((p for p in self.project.parts if p.id == seg.part_id), None)
        part_start = part.start if part else 0.0
        part_end = part.end if part else self.project.duration
        prev = self.project.segments[i - 1] if i and self.project.segments[i - 1].part_id == seg.part_id else None
        nxt = self.project.segments[i + 1] if i + 1 < len(self.project.segments) and self.project.segments[i + 1].part_id == seg.part_id else None
        lower = prev.start + .05 if prev else part_start
        upper = nxt.end - .05 if nxt else part_end
        if not lower <= start.value() < end.value() <= upper:
            self.error(self.tr('interval_error'))
            return
        seg.start = start.value(); seg.end = end.value()
        if prev: prev.end = seg.start
        if nxt: nxt.start = seg.end
        self.mark(); self.select(i); self.schedule_history()

    def project_snapshot(self):
        if not self.project:
            return None
        return {
            'reference_source': self.project.reference_source,
            'parts_confirmed': bool(getattr(self.project, 'parts_confirmed', False)),
            'parts': [(p.start, p.end, p.id) for p in self.project.parts],
            'segments': [
                {
                    'start': seg.start, 'end': seg.end, 'transcript': seg.transcript,
                    'title': seg.title, 'reference': seg.reference, 'take': seg.take,
                    'id': seg.id, 'part_id': seg.part_id,
                }
                for seg in self.project.segments
            ],
        }

    def reset_history(self):
        self.history_timer.stop()
        self.undo_history.clear()
        self.redo_history.clear()
        self.history_baseline = self.project_snapshot()

    def schedule_history(self, delay=0):
        if self.history_suspended or not self.project:
            return
        if delay <= 0:
            self.commit_history()
        else:
            self.history_timer.start(delay)

    def commit_history(self):
        if self.history_suspended or not self.project:
            return
        current = self.project_snapshot()
        if self.history_baseline is None:
            self.history_baseline = current
            return
        if current != self.history_baseline:
            self.undo_history.append(self.history_baseline)
            if len(self.undo_history) > 100:
                self.undo_history.pop(0)
            self.history_baseline = current
            self.redo_history.clear()

    def apply_project_snapshot(self, snapshot):
        if not self.project or snapshot is None:
            return
        self.history_suspended = True
        try:
            self.project.reference_source = snapshot['reference_source']
            self.project.parts_confirmed = bool(snapshot.get('parts_confirmed', bool(snapshot.get('segments'))))
            self.project.parts = [core.Part(a, b, pid) for a, b, pid in snapshot.get('parts', [(0.0, self.project.duration, 0)])]
            self.project.segments = [core.Segment(**state) for state in snapshot.get('segments', [])]
            self.division_mode = False
            self.division_markers = []
            self.manual_mode = False
            self.manual_start = None
            self.manual_split_history = []
            self.original.division_mode = False
            self.original.division_markers = []
            self.original.manual_division_mode = False
            self.original.project = self.project; self.dub.project = self.project
            self.dub.take_peaks = {}
            for seg in self.project.segments:
                if seg.take and (self.project.root / seg.take).is_file():
                    try:
                        self.dub.take_peaks[seg.id] = (
                            core.peaks(self.project.root / seg.take, 1000),
                            core.sf.info(self.project.root / seg.take).duration,
                        )
                    except Exception:
                        pass
            self.refresh_part_combo()
            if self.project.segments:
                self.reference.show(); self.track_scroll[1].show()
                self.select(min(self.index, len(self.project.segments) - 1))
            else:
                self.reference.hide(); self.ref_tools.hide(); self.track_scroll[1].hide()
            self.update_reference_controls(); self.update_structure_ui()
            self.mark()
            for track in (self.original, self.dub): track.update()
        finally:
            self.history_suspended = False

    def undo_project_change(self):
        if not self.project or self.recording or self.worker:
            return
        if self.history_timer.isActive():
            self.history_timer.stop()
            self.commit_history()
        if not self.undo_history:
            return
        current = self.project_snapshot()
        target = self.undo_history.pop()
        self.redo_history.append(current)
        self.apply_project_snapshot(target)
        self.history_baseline = target

    def redo_project_change(self):
        if not self.project or self.recording or self.worker:
            return
        if self.history_timer.isActive():
            self.history_timer.stop()
            self.commit_history()
        if not self.redo_history:
            return
        current = self.project_snapshot()
        target = self.redo_history.pop()
        self.undo_history.append(current)
        self.apply_project_snapshot(target)
        self.history_baseline = target

    def input_focused(self):
        return isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSlider))

    def mark_shortcut(self):
        if not self.project or self.worker or self.recording or self.input_focused():
            return

        # Before Parts have been confirmed, M is a direct 'split at playhead' command.
        # First press enters division mode and immediately places the first boundary;
        # every following press adds another shared end/start boundary at the needle.
        if not self.project.segments and not getattr(self.project, 'parts_confirmed', False):
            if not self.division_mode:
                self.begin_division()
            if self.division_mode:
                self.mark_part_end()
            return

        if self.division_mode:
            self.mark_part_end()
            return

        # Once Parts exist, M uses the exact same mental model inside the current
        # Part: the Part start is marker 1 and every press creates one shared
        # end/start boundary at the playhead.
        if not self.manual_mode:
            self.start_manual_chapters()
        if self.manual_mode:
            self.split_segment_at_playhead()

    def undo_mark_shortcut(self):
        if not self.project or self.worker or self.recording or self.input_focused():
            return
        if self.division_mode:
            self.undo_part_marker()
        elif self.manual_mode:
            self.undo_manual_split()

    def cancel_marking_shortcut(self):
        if self.division_mode:
            self.cancel_division()
        elif self.manual_mode:
            self.stop_manual_chapters()

    def _load_shortcuts(self):
        try:
            raw = self.settings.value('shortcuts/v1', '{}') or '{}'
            data = json.loads(raw) if isinstance(raw, str) else raw
            result = normalise(data)
            if find_conflict(result):
                return dict(DEFAULT_SHORTCUTS)
            return result
        except (ValueError, TypeError):
            return dict(DEFAULT_SHORTCUTS)

    def shortcut_text(self, action):
        """Show Command glyphs on Mac, familiar Ctrl+ labels on Windows."""
        return QKeySequence(self.shortcuts[action]).toString(QKeySequence.NativeText)

    def shortcut_settings(self):
        lang = LABELS.get(self.ui_language, LABELS['pt'])
        dialog = ModernDialog(self)
        dialog.setWindowTitle(lang['shortcuts'])
        dialog.resize(600, 640)
        root = QVBoxLayout(dialog.body)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)
        hint = QLabel(lang['shortcuts_hint'])
        hint.setWordWrap(True)
        root.addWidget(hint)

        # A vertical scroll area works even on smaller laptop displays.
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        root.addWidget(area, 1)
        content = QWidget()
        forms = QVBoxLayout(content)
        forms.setContentsMargins(0, 0, 5, 0)
        forms.setSpacing(10)
        editors = {}
        for group, actions in GROUPS.items():
            section = QGroupBox(lang[group])
            form = QFormLayout(section)
            form.setSpacing(10)
            for action in actions:
                entry = QKeySequenceEdit()
                entry.setKeySequence(QKeySequence(self.shortcuts[action]))
                entry.setToolTip(lang[action])
                entry.setMinimumWidth(170)
                form.addRow(lang[action], entry)
                editors[action] = entry
            forms.addWidget(section)
        forms.addStretch()
        area.setWidget(content)
        controls = QHBoxLayout()
        reset = QPushButton(lang['reset'])
        controls.addWidget(reset)
        controls.addStretch()
        cancel = QPushButton({'pt': 'Cancelar', 'en': 'Cancel', 'ja': 'キャンセル'}.get(self.ui_language, 'Cancelar'))
        save = QPushButton(lang['save_changes'])
        save.setObjectName('primaryButton')
        controls.addWidget(cancel)
        controls.addWidget(save)
        root.addLayout(controls)

        def reset_defaults():
            for action, editor in editors.items():
                editor.setKeySequence(QKeySequence(DEFAULT_SHORTCUTS[action]))

        def apply_shortcuts():
            candidate = {}
            for action, editor in editors.items():
                key = editor.keySequence()
                if key.isEmpty() or key.count() != 1:
                    QMessageBox.warning(dialog, lang['shortcuts'], lang['invalid'])
                    return
                candidate[action] = key.toString(QKeySequence.PortableText)
            collision = find_conflict(candidate)
            if collision:
                first, second = collision
                QMessageBox.warning(dialog, lang['shortcuts'],
                    lang['conflict'].format(action=lang[first] + ' / ' + lang[second]))
                return
            self.shortcuts = normalise(candidate)
            self.settings.setValue('shortcuts/v1', json.dumps(overrides(self.shortcuts), ensure_ascii=False))
            self.apply_language()
            dialog.accept()

        reset.clicked.connect(reset_defaults)
        cancel.clicked.connect(dialog.reject)
        save.clicked.connect(apply_shortcuts)
        dialog.exec()

    def _dispatch_shortcut(self, action):
        """Returns whether the shortcut is handled in the current context."""
        if action == 'open': self.open_project()
        elif action == 'save': self.save_project()
        elif action == 'save_as': self.save_project(True)
        elif action == 'close': self.close_project()
        elif action == 'play': self.toggle_play()
        elif action == 'record': self.record()
        elif action == 'play_take': self.play_take()
        elif action == 'undo': self.undo_project_change()
        elif action == 'redo': self.redo_project_change()
        elif action == 'mark': self.mark_shortcut()
        elif action == 'undo_mark': self.undo_mark_shortcut()
        elif action == 'confirm_division':
            if not self.division_mode:
                return False
            self.confirm_division()
        elif action == 'cancel_marking':
            if not (self.division_mode or self.manual_mode):
                return False
            self.cancel_marking_shortcut()
        elif action == 'next_chapter': self.next_segment()
        elif action == 'previous_chapter': self.previous_segment()
        elif action == 'seek_forward': self.seek_relative(1.0)
        elif action == 'seek_back': self.seek_relative(-1.0)
        else: return False
        return True

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress or not self.isActiveWindow() or QApplication.activeModalWidget():
            return super().eventFilter(obj, event)
        try:
            pressed = QKeySequence(event.keyCombination()).toString(QKeySequence.PortableText)
        except (TypeError, AttributeError):
            return super().eventFilter(obj, event)
        if pressed == 'Enter':
            pressed = 'Return'  # Numeric keypad confirm is equivalent to Return.
        current = {value: key for key, value in self.shortcuts.items()}
        action = current.get(pressed)
        if action is None:
            return super().eventFilter(obj, event)
        focus = QApplication.focusWidget()
        editing = self.input_focused()
        # Preserve ordinary typing, text editing and widget arrow navigation.
        # Ctrl/Cmd+S/O/W still work while a text field has the focus.
        if editing and action not in ('open', 'save', 'save_as', 'close'):
            return super().eventFilter(obj, event)
        if event.isAutoRepeat() and action not in ('seek_forward', 'seek_back'):
            return True
        if self._dispatch_shortcut(action):
            return True
        return super().eventFilter(obj, event)

    def next_segment(self):
        if not self.project or self.worker or self.recording or not self.project.segments:
            return
        part = self.current_part()
        indices = [i for i, seg in enumerate(self.project.segments) if not part or seg.part_id == part.id]
        later = [i for i in indices if i > self.index]
        if later:
            self.select(later[0])

    def previous_segment(self):
        if not self.project or self.worker or self.recording or not self.project.segments:
            return
        part = self.current_part()
        indices = [i for i, seg in enumerate(self.project.segments) if not part or seg.part_id == part.id]
        earlier = [i for i in indices if i < self.index]
        if earlier:
            self.select(earlier[-1])

    def seek_relative(self, seconds):
        if not self.project or self.worker or self.recording:
            return
        low, high = 0.0, self.project.duration
        if getattr(self.project, 'parts_confirmed', False):
            part = self.current_part()
            if part:
                low, high = part.start, part.end
        target = max(low, min(high, self.player.position() / 1000.0 + seconds))
        self.bound = None
        self.player.setPosition(round(target * 1000))

    def playback_state_changed(self, state):
        kind = 'pause' if state == QMediaPlayer.PlayingState and self.mode == 'original' and not self.recording else 'play'
        self.play_btn.setProperty('icon_kind', kind)
        self.play_btn.setIcon(icon(kind, '#e1dfea' if self.dark else '#626777'))
        self.play_btn.setToolTip(self.tr('pause') if kind == 'pause' else self.tr('continue_play'))

    def stop_playback(self):
        self.player.pause()
        self.dubplayer.stop()
        self.bound = None
        self.output.setMuted(False)
        self.mode = 'original'
        self.playback_state_changed(self.player.playbackState())

    def restart_segment(self):
        if not self.project or not self.project.segments or self.worker or self.recording or self.input_focused():
            return
        s = self.project.segments[self.index]
        self.dubplayer.stop()
        self.mode = 'original'
        self.output.setMuted(False)
        self.bound = s.end
        self.player.setPosition(round(s.start * 1000))
        self.player.play()

    def toggle_play(self):
        if not self.project or self.worker or self.recording or self.input_focused():
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState and self.mode == 'original':
            self.player.pause(); return
        self.dubplayer.stop(); self.mode = 'original'; self.output.setMuted(False)
        if not self.project.segments:
            if getattr(self.project, 'parts_confirmed', False):
                part = self.current_part()
                t = self.player.position() / 1000.0
                if part and (t < part.start - .02 or t >= part.end - .01):
                    self.player.setPosition(round(part.start * 1000))
                self.bound = part.end if part else None
            else:
                self.bound = None
            self.player.play()
            return
        seg = self.project.segments[self.index]
        t = self.player.position() / 1000
        if self.manual_mode:
            # Manual selection is free navigation inside the current part.
            self.bound = None
        else:
            if t < seg.start - .02 or t >= seg.end - .01:
                self.player.setPosition(round(seg.start * 1000))
            self.bound = seg.end
        self.player.play()

    def play_take(self):
        if not self.project or not self.project.segments or self.recording:
            return
        s = self.project.segments[self.index]
        if not s.take:
            return
        self.stop_playback()
        self.mode = 'dub'
        self.output.setMuted(True)
        self.bound = s.end
        self.player.setPosition(round(s.start * 1000))
        self.dubplayer.setSource(QUrl.fromLocalFile(str(self.project.root / s.take)))
        self.player.play(); self.dubplayer.play()

    def position_changed(self, ms):
        t = ms / 1000
        if self.bound is not None and t >= self.bound and not self.recording:
            self.player.pause(); self.dubplayer.stop(); self.output.setMuted(False); self.bound = None
        self.original.position = self.dub.position = t
        if self.project:
            self.clock.setText(f'{t // 60:02.0f}:{t % 60:05.2f} / {self.project.duration // 60:02.0f}:{self.project.duration % 60:05.2f}')
        self.original.update(); self.dub.update()

    def record(self):
        if self.recording:
            self.stop_recording(); return
        if not self.project or not self.project.segments or self.worker or self.input_focused():
            return
        s = self.project.segments[self.index]
        if s.take and not self.ask(self.tr('replace_take', n=self.original.chapter_number(self.index))):
            return
        self.stop_playback()
        name = f'takes/{uuid.uuid4().hex}.wav'
        path = self.project.root / name
        path.parent.mkdir(exist_ok=True)
        try:
            rec = Recorder(str(path), self.device, s.end - s.start)
            rec.start()
        except Exception as e:
            self.error(self.tr('mic_error', msg=e))
            return
        self.recording = rec
        self.pending_take = name
        self.output.setMuted(True)
        self.bound = s.end
        self.player.setPosition(round(s.start * 1000))
        self.player.play()
        self.dub.live = []
        self.dub.live_seconds = 0
        self.record_btn.setProperty('icon_kind', 'stop')
        self.record_btn.setIcon(icon('stop', '#ffffff'))
        self.record_btn.setToolTip(self.tr('stop_record'))
        self.set_enabled()
        self.timer.start()

    def tick(self):
        if not self.recording:
            return
        r = self.recording
        s = self.project.segments[self.index]
        self.dub.live.append(r.peak)
        self.dub.live_seconds = r.frames / core.RATE
        self.dub.position = s.start + self.dub.live_seconds
        self.dub.update()
        if r.frames >= r.limit or r.error:
            self.stop_recording()

    def stop_recording(self):
        if not self.recording:
            return
        self.timer.stop()
        r = self.recording
        r.stop()
        self.recording = None
        self.stop_playback()
        s = self.project.segments[self.index]
        if r.frames > 0 and not r.error:
            s.take = self.pending_take
            self.dub.take_peaks[s.id] = (core.peaks(self.project.root / s.take, 1000), r.frames / core.RATE)
            self.mark()
            self.schedule_history()
        else:
            (self.project.root / self.pending_take).unlink(missing_ok=True)
            self.error(r.error or 'O microfone não enviou áudio.')
        self.pending_take = None
        self.dub.live = []
        self.dub.update()
        self.record_btn.setProperty('icon_kind', 'mic')
        self.record_btn.setIcon(icon('mic', '#e1dfea' if self.dark else '#626777'))
        self.record_btn.setToolTip(self.tr('record').split(' · ')[0] + ' · ' + self.shortcut_text('record'))
        self.set_enabled()

    def save_project(self, save_as=False, after=None):
        if not self.project or self.worker or self.recording:
            return
        path = self.project.path
        if not path or save_as:
            path, _ = QFileDialog.getSaveFileName(self, self.tr('save_project'), path or self.tr('default_project_name'), 'DubStudio (*.dubstudio)')
            if not path:
                return
            if not path.lower().endswith('.dubstudio'):
                path += '.dubstudio'

        project = self.project
        def done(_):
            if self.project is not project:
                return
            self.project.path = path
            self.dirty = False
            self.setWindowTitle('DubStudio')
            if after:
                after()
        self.job('Salvando projeto com vídeo e gravações…', lambda _: core.save_project(project, path), done)

    def open_project(self):
        if not self.can_replace():
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('open_project_dialog'), '', 'DubStudio (*.dubstudio)')
        if path:
            def done(project):
                self.attach(project)
                self.dirty = False
                self.setWindowTitle('DubStudio')
            self.job('Abrindo projeto…', lambda _: core.load_project(path), done)

    def export(self):
        if not self.project or self.recording or self.worker:
            return
        missing = sum(not s.take for s in self.project.segments)
        if missing and not self.ask(self.tr('missing_takes', n=missing)):
            return
        d = ModernDialog(self)
        d.setWindowTitle(self.tr('export'))
        f = QFormLayout(d.body)
        c = QComboBox(); c.addItems(core.FORMATS)
        f.addRow(self.tr('format'), c)
        note = QLabel(self.tr('export_note'))
        note.setWordWrap(True); f.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(d.accept); bb.rejected.connect(d.reject); f.addRow(bb)
        if d.exec() != QDialog.Accepted:
            return
        fmt = c.currentText(); ext = core.FORMATS[fmt][0]
        path, _ = QFileDialog.getSaveFileName(self, self.tr('export'), self.tr('default_export_name', ext=ext), f'{fmt} (*.{ext})')
        if not path:
            return
        if not path.lower().endswith('.' + ext):
            path += '.' + ext
        self.job(self.tr('exporting'),
                 lambda _: core.export_project(self.project, path, fmt),
                 lambda _: QMessageBox.information(self, 'DubStudio', self.tr('export_done')))

    def preferences(self):
        import sounddevice as sd
        d = ModernDialog(self)
        d.setWindowTitle(self.tr('prefs_title'))
        d.setSizeGripEnabled(True)
        d.resize(620, 470)
        f = QFormLayout(d.body)

        ui_lang = QComboBox()
        ui_lang.addItem('Português', 'pt')
        ui_lang.addItem('English', 'en')
        ui_lang.addItem('日本語', 'ja')
        for i in range(ui_lang.count()):
            if ui_lang.itemData(i) == self.ui_language:
                ui_lang.setCurrentIndex(i)
                break
        f.addRow(self.tr('app_language'), ui_lang)

        shortcuts_button = QPushButton(display_label(self.ui_language, 'change'))
        shortcuts_button.clicked.connect(self.shortcut_settings)
        f.addRow(display_label(self.ui_language, 'shortcuts'), shortcuts_button)

        audio_lang = QComboBox()
        audio_lang.addItem(self.tr('audio_auto'), 'auto')
        audio_lang.addItem(self.tr('audio_pt'), 'pt')
        audio_lang.addItem(self.tr('audio_en'), 'en')
        audio_lang.addItem(self.tr('audio_ja'), 'ja')
        current_audio_language = self.project.language if self.project else self.language
        for i in range(audio_lang.count()):
            if audio_lang.itemData(i) == current_audio_language:
                audio_lang.setCurrentIndex(i)
                break
        f.addRow(self.tr('audio_language_title'), audio_lang)

        devices = QComboBox(); devices.addItem(self.tr('default_mic'), None)
        try:
            for i, device in enumerate(sd.query_devices()):
                if device['max_input_channels'] > 0:
                    devices.addItem(device['name'], i)
        except Exception:
            pass
        for i in range(devices.count()):
            if devices.itemData(i) == self.device:
                devices.setCurrentIndex(i)
        f.addRow(self.tr('microphone'), devices)

        model = QComboBox()
        for model_id, (name_key, desc_key) in MODEL_KEYS.items():
            model.addItem(self.tr(name_key), model_id)
        for i in range(model.count()):
            if model.itemData(i) == self.transcription_model:
                model.setCurrentIndex(i)
                break
        f.addRow(self.tr('transcription_model'), model)

        model_info = QLabel()
        model_info.setWordWrap(True)
        model_info.setObjectName('modelInfo')
        def update_model_info():
            model_id = model.currentData()
            _, desc_key = MODEL_KEYS.get(model_id, MODEL_KEYS['small'])
            model_info.setText(self.tr(desc_key) + '\n' + self.tr('model_estimate_note'))
        model.currentIndexChanged.connect(update_model_info)
        update_model_info()
        f.addRow(self.tr('model_cost'), model_info)

        note = QLabel(self.tr('prefs_note'))
        note.setWordWrap(True); f.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(d.accept); bb.rejected.connect(d.reject); f.addRow(bb)
        if d.exec() == QDialog.Accepted:
            self.device = devices.currentData()
            self.transcription_model = model.currentData()
            selected_audio_language = audio_lang.currentData()
            self.language = selected_audio_language
            self.settings.setValue('audio_language', selected_audio_language)
            if self.project and self.project.language != selected_audio_language:
                self.project.language = selected_audio_language
                self.mark()
            new_ui_language = ui_lang.currentData()
            self.settings.setValue('transcription_model', self.transcription_model)
            self.settings.setValue('ui_language', new_ui_language)
            if new_ui_language != self.ui_language:
                self.ui_language = new_ui_language
                self.apply_language()

    def closeEvent(self, event):
        if self.worker:
            self.error(self.tr('wait_operation'))
            event.ignore(); return
        if self.recording:
            self.stop_recording()
        if self.dirty and not self.ask(self.tr('close_discard')):
            event.ignore(); return
        self.stop_transcription()
        self.player.setSource(QUrl()); self.dubplayer.setSource(QUrl())
        if self.project:
            shutil.rmtree(self.project.root, ignore_errors=True)
        event.accept()


def main():
    # Set Windows AppUserModelID before the QApplication exists; this is needed
    # for correct pinned taskbar grouping and icon rendering on Windows.
    if os.name == 'nt':
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('DubStudio.DubStudio.Desktop')
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName('DubStudio')
    app.setOrganizationName('DubStudio')
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    candidates = [base / 'assets' / 'dubstudio.ico', base / 'assets' / 'dubstudio.png',
                  Path(__file__).resolve().parent.parent / 'assets' / 'dubstudio.png']
    for path in candidates:
        if path.is_file():
            app_icon = QIcon(str(path))
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                break
    app.setStyle('Fusion')
    window = Window()
    window.setWindowIcon(app.windowIcon())
    window.showMaximized()  # Maximized, NOT exclusive fullscreen; keeps OS titlebar/controls.
    sys.exit(app.exec())
