"""Portable shortcut presets and conflict validation.

This file has no Qt dependencies, so shortcuts can be checked in CI without
initialising audio/video or a graphical session.
"""
from __future__ import annotations

# Qt's portable names are used intentionally. On macOS, Ctrl in a QKeySequence
# is presented/mapped as Command according to Qt's platform conventions.
DEFAULT_SHORTCUTS = {
    'open': 'Ctrl+O',
    'save': 'Ctrl+S',
    'save_as': 'Ctrl+Shift+S',
    'close': 'Ctrl+W',
    'play': 'Space',
    'record': 'R',
    'play_take': 'D',
    'undo': 'Ctrl+Z',
    'redo': 'Ctrl+Shift+Z',
    'mark': 'M',
    'undo_mark': 'Shift+M',
    'confirm_division': 'Return',
    'cancel_marking': 'Esc',
    'next_chapter': 'Up',
    'previous_chapter': 'Down',
    'seek_forward': 'Right',
    'seek_back': 'Left',
}

GROUPS = {
    'project': ('open', 'save', 'save_as', 'close'),
    'playback': ('play', 'record', 'play_take', 'next_chapter',
                 'previous_chapter', 'seek_forward', 'seek_back'),
    'editing': ('undo', 'redo', 'mark', 'undo_mark',
                'confirm_division', 'cancel_marking'),
}

LABELS = {
    'pt': {
        'project': 'Projeto', 'playback': 'Reprodução e gravação', 'editing': 'Edição e capítulos',
        'open': 'Abrir projeto', 'save': 'Salvar', 'save_as': 'Salvar como', 'close': 'Fechar projeto',
        'play': 'Reproduzir / pausar', 'record': 'Gravar / parar', 'play_take': 'Ouvir gravação',
        'undo': 'Desfazer', 'redo': 'Refazer', 'mark': 'Marcar ponto',
        'undo_mark': 'Desfazer marcação', 'confirm_division': 'Confirmar divisão',
        'cancel_marking': 'Cancelar marcação', 'next_chapter': 'Próximo capítulo',
        'previous_chapter': 'Capítulo anterior', 'seek_forward': 'Avançar um segundo',
        'seek_back': 'Voltar um segundo', 'shortcuts': 'Atalhos do teclado',
        'shortcuts_hint': 'Selecione um atalho e pressione a nova combinação. Alterações são aplicadas ao salvar.',
        'reset': 'Restaurar padrões', 'change': 'Personalizar…',
        'conflict': 'Essa combinação já está atribuída a: {action}.',
        'invalid': 'Escolha uma combinação válida para cada ação.',
        'save_changes': 'Salvar atalhos',
    },
    'en': {
        'project': 'Project', 'playback': 'Playback and recording', 'editing': 'Editing and chapters',
        'open': 'Open project', 'save': 'Save', 'save_as': 'Save as', 'close': 'Close project',
        'play': 'Play / pause', 'record': 'Record / stop', 'play_take': 'Play recording',
        'undo': 'Undo', 'redo': 'Redo', 'mark': 'Mark point',
        'undo_mark': 'Undo marker', 'confirm_division': 'Confirm division',
        'cancel_marking': 'Cancel marking', 'next_chapter': 'Next chapter',
        'previous_chapter': 'Previous chapter', 'seek_forward': 'Seek forward one second',
        'seek_back': 'Seek backward one second', 'shortcuts': 'Keyboard shortcuts',
        'shortcuts_hint': 'Select a shortcut and type a new combination. Changes apply when saved.',
        'reset': 'Restore defaults', 'change': 'Customize…',
        'conflict': 'This combination is already used by: {action}.',
        'invalid': 'Choose a valid key combination for every action.',
        'save_changes': 'Save shortcuts',
    },
    'ja': {
        'project': 'プロジェクト', 'playback': '再生と録音', 'editing': '編集とチャプター',
        'open': 'プロジェクトを開く', 'save': '保存', 'save_as': '名前を付けて保存', 'close': 'プロジェクトを閉じる',
        'play': '再生 / 一時停止', 'record': '録音 / 停止', 'play_take': '録音を再生',
        'undo': '元に戻す', 'redo': 'やり直す', 'mark': 'マーカーを追加',
        'undo_mark': 'マーカーを元に戻す', 'confirm_division': '分割を確定',
        'cancel_marking': 'マーカーをキャンセル', 'next_chapter': '次のチャプター',
        'previous_chapter': '前のチャプター', 'seek_forward': '1秒進む',
        'seek_back': '1秒戻る', 'shortcuts': 'キーボードショートカット',
        'shortcuts_hint': '項目を選択し、新しいキーを入力してください。保存後に適用されます。',
        'reset': '初期設定に戻す', 'change': 'カスタマイズ…',
        'conflict': 'このキーはすでに使用されています：{action}',
        'invalid': 'すべての項目に有効なキーを指定してください。',
        'save_changes': 'ショートカットを保存',
    },
}


def normalise(mapping):
    """Build full mapping from user overrides; unknown actions are ignored."""
    clean = dict(DEFAULT_SHORTCUTS)
    if isinstance(mapping, dict):
        for action, key in mapping.items():
            if action in clean and isinstance(key, str) and key.strip():
                clean[action] = key.strip()
    return clean


def find_conflict(mapping):
    """Return the first two colliding action ids or None."""
    seen = {}
    for action, combination in normalise(mapping).items():
        # Portability normalization (e.g. Ctrl+S) is handled by Qt on read/write.
        canonical = combination.strip().casefold()
        if canonical in seen:
            return seen[canonical], action
        seen[canonical] = action
    return None


def overrides(mapping):
    merged = normalise(mapping)
    return {key: val for key, val in merged.items() if val != DEFAULT_SHORTCUTS[key]}


def display_label(lang, action):
    return LABELS.get(lang, LABELS['pt']).get(action, action)
