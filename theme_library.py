"""
@file theme_library.py
@brief Üçüncü parti hazır renk temaları (veri) — themes.builtin_packs() bunları ekler.

@details ÜRETİLMİŞ veri: KiCad renk teması dosyalarından `themes.parse_pack` ile
normalize edilip yalnız kullandığımız anahtarlar alındı (v2.40.0). Kaynaklar,
lisansları dağıtıma izin veren temalardır (CC0-1.0 / MIT / Apache-2.0); MIT ve
Apache lisansının istediği telif ve izin bildirimi `themes.notices_text()` ile
uygulamanın içinde gösterilir (Renk Temaları → Lisanslar…).

Seçim ölçüme dayanır (bkz. CLAUDE.md "Renk temaları"): board bölümü KiCad'in
varsayılan board renklerinin ya da başka bir hazır temanın birebir kopyası olan
temalarda board alınmadı (tokyo-night-hy, hartia, nuova-elettronica →
KiCad varsayılanı; dragonmux → Eagle Dark); şematiği Dracula'nın birebir
kopyası olan Vampire hiç alınmadı. KiCadMaxColors alınmadı: siyah zeminde parlak
dolu gövde okunurluk kuralını (zemin ve gövde aynı tarafta) karşılamıyor, lisansı
da belirsiz (paket CC0, depo MIT ve telif satırı boş).
"""

# (id, ad, şematik | None, board | None, kaynak, telif sahibi, SPDX lisans)
LIBRARY = [
    {'id': 'catppuccin-latte', 'name': 'Catppuccin Latte',
     'source': 'https://github.com/catppuccin/kicad',
     'copyright': 'Copyright (c) 2021 Catppuccin', 'license': 'MIT',
     'schematic': {'background': '#eff1f5', 'wire': '#4c4f69', 'bus': '#7287fd', 'junction': '#4c4f69',
      'component_outline': '#8839ef', 'component_body': '#e6e9ef', 'pin': '#1e66f5', 'pin_name':
      '#1e66f5', 'pin_number': '#7287fd', 'reference': '#5c5f77', 'value': '#5c5f77', 'fields':
      '#1e66f5', 'label_local': '#5c5f77', 'label_global': '#8839ef', 'label_hier': '#dc8a78',
      'sheet': '#40a02b', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#df8e1d',
      'sheet_filename': '#df8e1d', 'sheet_label': '#dc8a78', 'no_connect': '#7287fd', 'note':
      '#7287fd', 'worksheet': '#4c4f69'},
     'board': {'background': '#eff1f5', 'edge_cuts': '#4c4f69', 'f_silks': '#6c6f85', 'b_silks':
      '#5c5f77', 'f_mask': 'rgba(136,57,239,0.4)', 'b_mask': 'rgba(4,165,229,0.4)', 'f_paste':
      'rgba(23,146,153,0.9)', 'b_paste': 'rgba(32,159,181,0.9)', 'f_crtyd': '#8839ef',
      'b_crtyd': '#04a5e5', 'f_fab': '#afafaf', 'b_fab': '#585d84', 'pad_through_hole':
      '#df8e1d', 'via_through': '#9ca0b0', 'margin': '#7287fd', 'dwgs_user': '#9ca0b0',
      'cmts_user': '#8c8fa1', 'eco1_user': '#b4dbd2', 'eco2_user': '#d8c852', 'user_1':
      '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852', 'user_5':
      '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852', 'user_9':
      '#e8b2a7', 'copper': {'f': '#d20f39', 'b': '#1e66f5', 'in1': '#40a02b', 'in2': '#df8e1d',
      'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7',
      'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12':
      '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1',
      'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21':
      '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb',
      'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30':
      '#f2eda1'}}},
    {'id': 'catppuccin-frappe', 'name': 'Catppuccin Frappé',
     'source': 'https://github.com/catppuccin/kicad',
     'copyright': 'Copyright (c) 2021 Catppuccin', 'license': 'MIT',
     'schematic': {'background': '#303446', 'wire': '#c6d0f5', 'bus': '#babbf1', 'junction': '#c6d0f5',
      'component_outline': '#ca9ee6', 'component_body': '#292c3c', 'pin': '#8caaee', 'pin_name':
      '#8caaee', 'pin_number': '#babbf1', 'reference': '#b5bfe2', 'value': '#b5bfe2', 'fields':
      '#8caaee', 'label_local': '#b5bfe2', 'label_global': '#ca9ee6', 'label_hier': '#f2d5cf',
      'sheet': '#a6d189', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#e5c890',
      'sheet_filename': '#e5c890', 'sheet_label': '#f2d5cf', 'no_connect': '#babbf1', 'note':
      '#babbf1', 'worksheet': '#c6d0f5'},
     'board': {'background': '#303446', 'edge_cuts': '#c6d0f5', 'f_silks': '#a5adce', 'b_silks':
      '#b5bfe2', 'f_mask': 'rgba(202,158,230,0.4)', 'b_mask': 'rgba(153,209,219,0.4)',
      'f_paste': 'rgba(129,200,190,0.9)', 'b_paste': 'rgba(133,193,220,0.9)', 'f_crtyd':
      '#ca9ee6', 'b_crtyd': '#99d1db', 'f_fab': '#afafaf', 'b_fab': '#585d84',
      'pad_through_hole': '#e5c890', 'via_through': '#737994', 'margin': '#babbf1', 'dwgs_user':
      '#737994', 'cmts_user': '#838ba7', 'eco1_user': '#b4dbd2', 'eco2_user': '#d8c852',
      'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852',
      'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852',
      'user_9': '#e8b2a7', 'copper': {'f': '#e78284', 'b': '#8caaee', 'in1': '#a6d189', 'in2':
      '#e5c890', 'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7':
      '#e8b2a7', 'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb',
      'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16':
      '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6',
      'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25':
      '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7',
      'in30': '#f2eda1'}}},
    {'id': 'catppuccin-macchiato', 'name': 'Catppuccin Macchiato',
     'source': 'https://github.com/catppuccin/kicad',
     'copyright': 'Copyright (c) 2021 Catppuccin', 'license': 'MIT',
     'schematic': {'background': '#24273a', 'wire': '#cad3f5', 'bus': '#b7bdf8', 'junction': '#cad3f5',
      'component_outline': '#c6a0f6', 'component_body': '#1e2030', 'pin': '#8aadf4', 'pin_name':
      '#8aadf4', 'pin_number': '#b7bdf8', 'reference': '#b8c0e0', 'value': '#b8c0e0', 'fields':
      '#8aadf4', 'label_local': '#b8c0e0', 'label_global': '#c6a0f6', 'label_hier': '#f4dbd6',
      'sheet': '#a6da95', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#eed49f',
      'sheet_filename': '#eed49f', 'sheet_label': '#f4dbd6', 'no_connect': '#b7bdf8', 'note':
      '#b7bdf8', 'worksheet': '#cad3f5'},
     'board': {'background': '#24273a', 'edge_cuts': '#cad3f5', 'f_silks': '#a5adcb', 'b_silks':
      '#b8c0e0', 'f_mask': 'rgba(198,160,246,0.4)', 'b_mask': 'rgba(145,215,227,0.4)',
      'f_paste': 'rgba(139,213,202,0.9)', 'b_paste': 'rgba(125,196,228,0.9)', 'f_crtyd':
      '#c6a0f6', 'b_crtyd': '#91d7e3', 'f_fab': '#afafaf', 'b_fab': '#585d84',
      'pad_through_hole': '#eed49f', 'via_through': '#6e738d', 'margin': '#b7bdf8', 'dwgs_user':
      '#6e738d', 'cmts_user': '#8087a2', 'eco1_user': '#b4dbd2', 'eco2_user': '#d8c852',
      'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852',
      'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852',
      'user_9': '#e8b2a7', 'copper': {'f': '#ed8796', 'b': '#8aadf4', 'in1': '#a6da95', 'in2':
      '#eed49f', 'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7':
      '#e8b2a7', 'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb',
      'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16':
      '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6',
      'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25':
      '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7',
      'in30': '#f2eda1'}}},
    {'id': 'catppuccin-mocha', 'name': 'Catppuccin Mocha',
     'source': 'https://github.com/catppuccin/kicad',
     'copyright': 'Copyright (c) 2021 Catppuccin', 'license': 'MIT',
     'schematic': {'background': '#1e1e2e', 'wire': '#cdd6f4', 'bus': '#b4befe', 'junction': '#cdd6f4',
      'component_outline': '#cba6f7', 'component_body': '#181825', 'pin': '#89b4fa', 'pin_name':
      '#89b4fa', 'pin_number': '#b4befe', 'reference': '#bac2de', 'value': '#bac2de', 'fields':
      '#89b4fa', 'label_local': '#bac2de', 'label_global': '#cba6f7', 'label_hier': '#f5e0dc',
      'sheet': '#a6e3a1', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#f9e2af',
      'sheet_filename': '#f9e2af', 'sheet_label': '#f5e0dc', 'no_connect': '#b4befe', 'note':
      '#b4befe', 'worksheet': '#cdd6f4'},
     'board': {'background': '#1e1e2e', 'edge_cuts': '#cdd6f4', 'f_silks': '#a6adc8', 'b_silks':
      '#bac2de', 'f_mask': 'rgba(203,166,247,0.4)', 'b_mask': 'rgba(137,220,235,0.4)',
      'f_paste': 'rgba(148,226,213,0.9)', 'b_paste': 'rgba(116,199,236,0.9)', 'f_crtyd':
      '#cba6f7', 'b_crtyd': '#89dceb', 'f_fab': '#afafaf', 'b_fab': '#585d84',
      'pad_through_hole': '#f9e2af', 'via_through': '#6c7086', 'margin': '#b4befe', 'dwgs_user':
      '#6c7086', 'cmts_user': '#7f849c', 'eco1_user': '#b4dbd2', 'eco2_user': '#d8c852',
      'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852',
      'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852',
      'user_9': '#e8b2a7', 'copper': {'f': '#f38ba8', 'b': '#89b4fa', 'in1': '#a6e3a1', 'in2':
      '#f9e2af', 'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7':
      '#e8b2a7', 'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb',
      'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16':
      '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6',
      'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25':
      '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7',
      'in30': '#f2eda1'}}},
    {'id': 'dracula', 'name': 'Dracula',
     'source': 'https://github.com/dracula/kicad',
     'copyright': 'Copyright (c) 2020 Dracula Theme', 'license': 'MIT',
     'schematic': {'background': '#282936', 'wire': '#00f769', 'bus': '#62d6e8', 'junction': '#00f769',
      'component_outline': '#ea51b2', 'component_body': '#4d4f68', 'pin': '#ea51b2', 'pin_name':
      '#00f769', 'pin_number': '#ea51b2', 'reference': '#a1efe4', 'value': '#a1efe4', 'fields':
      '#a1efe4', 'label_local': '#ebff87', 'label_global': '#ff79c6', 'label_hier': '#ebff87',
      'sheet': '#b45bcf', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#b45bcf',
      'sheet_filename': '#b45bcf', 'sheet_label': '#b45bcf', 'no_connect': '#62d6e8', 'note':
      '#62d6e8', 'worksheet': '#b45bcf'},
     'board': {'background': '#282a36', 'edge_cuts': '#ffb86c', 'f_silks': '#8be9fd', 'b_silks':
      '#bd93f9', 'f_mask': '#bd93f9', 'b_mask': '#ffb86c', 'f_paste': '#ff5555', 'b_paste':
      '#ff5555', 'f_crtyd': '#44475a', 'b_crtyd': '#50fa7b', 'f_fab': '#848484', 'b_fab':
      '#8be9fd', 'pad_through_hole': '#ffb86c', 'via_through': '#44475a', 'margin': '#ff79c6',
      'dwgs_user': '#6272a4', 'cmts_user': '#8be9fd', 'eco1_user': '#50fa7b', 'eco2_user':
      '#ffb86c', 'copper': {'f': '#ff5555', 'b': '#50fa7b', 'in1': '#f1fa8c', 'in2': '#ff79c6',
      'in3': '#bd93f9', 'in4': '#6272a4', 'in5': '#50fa7b', 'in6': '#8be9fd', 'in7': '#ffb86c',
      'in8': '#840084', 'in9': '#44475a', 'in10': '#840084', 'in11': '#ff5555', 'in12':
      '#ffb86c', 'in13': '#44475a', 'in14': '#8be9fd', 'in15': '#50fa7b', 'in16': '#ff5555',
      'in17': '#f1fa8c', 'in18': '#ff79c6', 'in19': '#bd93f9', 'in20': '#8be9fd', 'in21':
      '#50fa7b', 'in22': '#8be9fd', 'in23': '#50fa7b', 'in24': '#840084', 'in25': '#44475a',
      'in26': '#840084', 'in27': '#ff5555', 'in28': '#ffb86c', 'in29': '#44475a', 'in30':
      '#8be9fd'}}},
    {'id': 'tokyo-night', 'name': 'Tokyo Night',
     'source': 'https://github.com/kevontheweb/tokyo-night-kicad-theme',
     'copyright': 'Copyright (c) 2018-present kevontheweb', 'license': 'MIT',
     'schematic': {'background': '#16161e', 'wire': '#bb9af7', 'bus': '#2ac3de', 'junction': '#c0caf5',
      'component_outline': '#7dcfff', 'component_body': '#414868', 'pin': '#9ece6a', 'pin_name':
      '#73daca', 'pin_number': '#9ece6a', 'reference': '#b4f9f8', 'value': '#b4f9f8', 'fields':
      '#bb9af7', 'label_local': '#c0caf5', 'label_global': '#e0af68', 'label_hier': '#73daca',
      'sheet': '#a9b1d6', 'sheet_background': '#24283b', 'sheet_name': '#2ac3de',
      'sheet_filename': '#565f89', 'sheet_label': '#9ece6a', 'no_connect': '#f7768e', 'note':
      '#565f89', 'worksheet': '#414868'},
     'board': {'background': '#16161e', 'edge_cuts': '#a9b1d6', 'f_silks': '#e6e7ed', 'b_silks':
      '#8896d8', 'f_mask': 'rgba(90,62,142,0.502)', 'b_mask': 'rgba(15,75,110,0.502)',
      'f_paste': 'rgba(140,67,81,0.8)', 'b_paste': 'rgba(51,99,92,0.788)', 'f_crtyd': '#bb9af7',
      'b_crtyd': '#7dcfff', 'f_fab': '#414868', 'b_fab': '#414868', 'pad_through_hole':
      '#e0af68', 'via_through': '#cfc9c2', 'margin': '#b4f9f8', 'dwgs_user': '#6c6e75',
      'cmts_user': '#5994dc', 'eco1_user': '#565f89', 'eco2_user': '#565f89', 'user_1':
      '#565f89', 'user_2': '#565f89', 'user_3': '#565f89', 'user_4': '#565f89', 'user_5':
      '#565f89', 'user_6': '#565f89', 'user_7': '#565f89', 'user_8': '#565f89', 'user_9':
      '#565f89', 'copper': {'f': '#f7768e', 'b': '#7aa2f7', 'in1': '#9ece6a', 'in2': '#ff9e64',
      'in3': '#73daca', 'in4': '#db628b', 'in5': '#bb9af7', 'in6': '#2ac3de', 'in7': '#e8b2a7',
      'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12':
      '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1',
      'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21':
      '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb',
      'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30':
      '#f2eda1'}}},
    {'id': 'tokyo-night-hy', 'name': 'Tokyo Night (H. Yamamoto)',
     'source': 'https://github.com/mjm-12/kicad-tokyo-night-schematic',
     'copyright': 'Copyright (c) 2026 Hayata Yamamoto', 'license': 'MIT',
     'schematic': {'background': '#1a1b26', 'wire': '#a9b1d6', 'bus': '#7aa2f7', 'junction': '#a9b1d6',
      'component_outline': '#a9b1d6', 'component_body': '#24283b', 'pin': '#a9b1d6', 'pin_name':
      '#7aa2f7', 'pin_number': '#e0af68', 'reference': '#7aa2f7', 'value': '#7aa2f7', 'fields':
      '#bb9af7', 'label_local': '#c0caf5', 'label_global': '#9ece6a', 'label_hier': '#e0af68',
      'sheet': '#7aa2f7', 'sheet_background': 'rgba(0,0,0,0)', 'sheet_name': '#7aa2f7',
      'sheet_filename': '#e0af68', 'sheet_label': '#7aa2f7', 'no_connect': '#f7768e', 'note':
      '#bfa0f7', 'worksheet': '#565f89'},
     'board': None},
    {'id': 'gruvbox', 'name': 'Gruvbox',
     'source': 'https://github.com/AlexanderBrevig/kicad-gruvbox-theme',
     'copyright': 'Copyright (c) 2021 Alexander Brevig', 'license': 'MIT',
     'schematic': {'background': '#1d2021', 'wire': '#789d6a', 'bus': '#8ec07c', 'junction': '#8ec07c',
      'component_outline': '#83a598', 'component_body': '#32302f', 'pin': '#689d6a', 'pin_name':
      '#d5c4a1', 'pin_number': '#fabd2f', 'reference': '#fbf1c7', 'value': '#fbf1c7', 'fields':
      '#840084', 'label_local': '#d65d0e', 'label_global': '#fe8019', 'label_hier': '#fe8019',
      'sheet': '#d65d0e', 'sheet_background': '#282828', 'sheet_name': '#ebdbb2',
      'sheet_filename': '#bdae93', 'sheet_label': '#fabd2f', 'no_connect': '#fb4934', 'note':
      '#ebdbb2', 'worksheet': '#ebdbb2'},
     'board': {'background': '#1d2021', 'edge_cuts': '#fabd2f', 'f_silks': '#ebdbb2', 'b_silks':
      '#ebdbb2', 'f_mask': '#a89984', 'b_mask': '#a89984', 'f_paste': '#a89984', 'b_paste':
      '#a89984', 'f_crtyd': '#b16286', 'b_crtyd': '#689d6a', 'f_fab': '#d5c4a1', 'b_fab':
      '#d5c4a1', 'pad_through_hole': '#d65d0e', 'via_through': '#ececec', 'margin': '#d3869b',
      'dwgs_user': '#c2c2c2', 'cmts_user': '#8ec07c', 'eco1_user': '#83a598', 'eco2_user':
      '#fabd2f', 'user_1': '#c2c2c2', 'user_2': '#458588', 'user_3': '#b4dbd2', 'user_4':
      '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8':
      '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#b8bb26', 'b': '#83a598', 'in1':
      '#d3869b', 'in2': '#8ec07c', 'in3': '#d3869b', 'in4': '#689d6a', 'in5': '#98971a', 'in6':
      '#d79921', 'in7': '#458588', 'in8': '#b16286', 'in9': '#8dcb81', 'in10': '#ed7c33',
      'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15':
      '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e',
      'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24':
      '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9',
      'in29': '#e8b2a7', 'in30': '#f2eda1'}}},
    {'id': 'gruvbox-light', 'name': 'Gruvbox Light',
     'source': 'https://github.com/hza2002/kicad-gruvbox-light-theme',
     'copyright': 'Copyright (c) 2024 Hu Ziang', 'license': 'MIT',
     'schematic': {'background': '#f9f5d7', 'wire': '#789d6a', 'bus': '#427b58', 'junction': '#427b58',
      'component_outline': '#076678', 'component_body': '#f2e5bc', 'pin': '#689d6a', 'pin_name':
      '#504945', 'pin_number': '#b57614', 'reference': '#3c3840', 'value': '#3c3836', 'fields':
      '#840084', 'label_local': '#d65d0e', 'label_global': '#af3a03', 'label_hier': '#af3a03',
      'sheet': '#d65d0e', 'sheet_background': '#fdf4c1', 'sheet_name': '#3c3836',
      'sheet_filename': '#665c54', 'sheet_label': '#b57614', 'no_connect': '#9d0006', 'note':
      '#3c3836', 'worksheet': '#3c3836'},
     'board': {'background': '#f9f5d7', 'edge_cuts': '#b57614', 'f_silks': '#3c3836', 'b_silks':
      '#3c3836', 'f_mask': '#7c6f64', 'b_mask': '#7c6f64', 'f_paste': '#7c6f64', 'b_paste':
      '#7c6f64', 'f_crtyd': '#b16286', 'b_crtyd': '#689d6a', 'f_fab': '#504945', 'b_fab':
      '#504945', 'pad_through_hole': '#d65d0e', 'via_through': '#ececec', 'margin': '#8f3f71',
      'dwgs_user': '#c2c2c2', 'cmts_user': '#427b58', 'eco1_user': '#076678', 'eco2_user':
      '#b57614', 'user_1': '#c2c2c2', 'user_2': '#458588', 'user_3': '#b4dbd2', 'user_4':
      '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8':
      '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#79740e', 'b': '#076678', 'in1':
      '#8f3f71', 'in2': '#427b58', 'in3': '#8f3f71', 'in4': '#689d6a', 'in5': '#98971a', 'in6':
      '#d79921', 'in7': '#458588', 'in8': '#b16286', 'in9': '#8dcb81', 'in10': '#ed7c33',
      'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15':
      '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e',
      'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24':
      '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9',
      'in29': '#e8b2a7', 'in30': '#f2eda1'}}},
    {'id': 'witchhazel', 'name': 'Witch Hazel',
     'source': 'https://github.com/theacodes/witchhazel',
     'copyright': 'Alethea Katherine Flowers', 'license': 'Apache-2.0',
     'schematic': {'background': '#131218', 'wire': '#ae81ff', 'bus': '#81eeff', 'junction': '#dcc8ff',
      'component_outline': '#c5a3ff', 'component_body': '#433e56', 'pin': '#81ffbe', 'pin_name':
      '#81ffbe', 'pin_number': '#64cb96', 'reference': '#81eeff', 'value': '#81eeff', 'fields':
      '#ae81ff', 'label_local': '#dcc8ff', 'label_global': '#fff781', 'label_hier': '#a3ffcf',
      'sheet': '#ae81ff', 'sheet_background': '#131218', 'sheet_name': '#81eeff',
      'sheet_filename': '#4e8189', 'sheet_label': '#81ffbe', 'no_connect': '#ff81ad', 'note':
      '#f8f8f0', 'worksheet': '#634e89'},
     'board': {'background': '#131218', 'edge_cuts': '#81ffbe', 'f_silks': '#dcc8ff', 'b_silks':
      '#8864cb', 'f_mask': '#894e63', 'b_mask': 'rgba(78,129,137,0.8)', 'f_paste':
      'rgba(252,249,255,0.502)', 'b_paste': 'rgba(167,234,255,0.502)', 'f_crtyd': '#ae81ff',
      'b_crtyd': '#ae81ff', 'f_fab': '#716799', 'b_fab': '#716799', 'pad_through_hole':
      '#e3d12e', 'via_through': '#e3d12e', 'margin': '#4e896b', 'dwgs_user': '#f8f8f0',
      'cmts_user': '#81ffbe', 'eco1_user': '#81eeff', 'eco2_user': '#ff81ad', 'user_1':
      '#c27600', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4': '#d8c852', 'user_5':
      '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8': '#d8c852', 'user_9':
      '#e8b2a7', 'copper': {'f': '#e27299', 'b': '#6fccdb', 'in1': '#7fc87f', 'in2': '#ce7d2c',
      'in3': '#4fcbcb', 'in4': '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7',
      'in8': '#f2eda1', 'in9': '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12':
      '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1',
      'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21':
      '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb',
      'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30':
      '#f2eda1'}}},
    {'id': 'monokai-hc', 'name': 'Monokai High Contrast',
     'source': 'https://github.com/74th/kicad-highcontrast-monokai-theme',
     'copyright': 'Copyright (c) 2022 Atsushi Morimoto (@74th)', 'license': 'MIT',
     'schematic': {'background': '#000000', 'wire': '#a6e22e', 'bus': '#a6e22e', 'junction': '#a6e22e',
      'component_outline': '#e6db74', 'component_body': '#222222', 'pin': '#e6db74', 'pin_name':
      '#fcfcfc', 'pin_number': '#fcfcfc', 'reference': '#fcfcfc', 'value': '#fcfcfc', 'fields':
      '#8000a0', 'label_local': '#e6db74', 'label_global': '#fcfcfc', 'label_hier': '#ae81ff',
      'sheet': '#f57f00', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#f57f00',
      'sheet_filename': '#f57f00', 'sheet_label': '#fcfcfc', 'no_connect': '#a6e22e', 'note':
      '#66d9ef', 'worksheet': '#8f8f8f'},
     'board': {'background': '#000000', 'edge_cuts': '#ffffff', 'f_silks': '#e7dc60', 'b_silks':
      '#5ccaef', 'f_mask': 'rgba(253,151,31,0.459)', 'b_mask': 'rgba(174,129,255,0.459)',
      'f_paste': '#fd3f04', 'b_paste': '#561cff', 'f_crtyd': '#773e00', 'b_crtyd':
      'rgba(67,186,216,0.459)', 'f_fab': 'rgba(253,151,31,0.565)', 'b_fab':
      'rgba(174,129,255,0.565)', 'pad_through_hole': '#ff26e2', 'via_through': '#ff26e2',
      'margin': '#ffffff', 'dwgs_user': '#c2c2c2', 'cmts_user': '#5994dc', 'eco1_user':
      '#ffffff', 'eco2_user': '#8f8f8f', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3':
      '#b4dbd2', 'user_4': '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7':
      '#b4dbd2', 'user_8': '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#f57f00', 'b':
      '#a57fff', 'in1': '#7fc87f', 'in2': '#ce7d2c', 'in3': '#4fcbcb', 'in4': '#db628b', 'in5':
      '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7', 'in8': '#f2eda1', 'in9': '#8dcb81', 'in10':
      '#ed7c33', 'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6', 'in14': '#28ccd9',
      'in15': '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18': '#5bc3eb', 'in19':
      '#f76f8e', 'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7', 'in23': '#f2eda1',
      'in24': '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27': '#a7a5c6', 'in28':
      '#28ccd9', 'in29': '#e8b2a7', 'in30': '#f2eda1'}}},
    {'id': 'skyline', 'name': 'Skyline',
     'source': 'https://github.com/CloverGit/kicad-theme-skyline',
     'copyright': 'Copyright (c) 2024 CloverGit', 'license': 'MIT',
     'schematic': {'background': '#1e2125', 'wire': '#64aabe', 'bus': '#268bd2', 'junction': '#64aabe',
      'component_outline': '#1b90b3', 'component_body': '#1a606e', 'pin': '#1b90b3', 'pin_name':
      '#c8824b', 'pin_number': '#dd8200', 'reference': '#a0dc6e', 'value': '#a0dc6e', 'fields':
      '#93a1a1', 'label_local': '#2aa198', 'label_global': '#4687a0', 'label_hier': '#1b90b3',
      'sheet': '#586e75', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#b1006d',
      'sheet_filename': '#18a1cc', 'sheet_label': '#df5218', 'no_connect': '#18d4ff', 'note':
      '#2fa0b3', 'worksheet': '#efbe48'},
     'board': {'background': '#001023', 'edge_cuts': '#d0d2cd', 'f_silks': '#cfe0e5', 'b_silks':
      '#c0d4d4', 'f_mask': '#ae4e00', 'b_mask': '#005d7c', 'f_paste': '#ffa96f', 'b_paste':
      '#95e5ff', 'f_crtyd': '#c2c2c2', 'b_crtyd': '#848484', 'f_fab': '#798596', 'b_fab':
      '#987d7e', 'pad_through_hole': '#c0c0c0', 'via_through': '#c0c0c0', 'margin': '#ff26e2',
      'dwgs_user': '#d8dee9', 'cmts_user': '#5994dc', 'eco1_user': '#008400', 'eco2_user':
      '#c2c200', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4':
      '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8':
      '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': '#1b90b3', 'b': '#28bebe', 'in1':
      '#18d4ff', 'in2': '#a9dd00', 'in3': '#004db1', 'in4': '#ddaf00', 'in5': '#b1006d', 'in6':
      '#ff8b44', 'in7': '#18d4ff', 'in8': '#dd8200', 'in9': '#004db1', 'in10': '#ddaf00',
      'in11': '#b1006d', 'in12': '#ff8b44', 'in13': '#18d4ff', 'in14': '#dd8200', 'in15':
      '#004db1', 'in16': '#ddaf00', 'in17': '#b1006d', 'in18': '#ff8b44', 'in19': '#18d4ff',
      'in20': '#dd8200', 'in21': '#004db1', 'in22': '#ddaf00', 'in23': '#b1006d', 'in24':
      '#ff8b44', 'in25': '#18d4ff', 'in26': '#dd8200', 'in27': '#004db1', 'in28': '#ddaf00',
      'in29': '#b1006d', 'in30': '#ff8b44'}}},
    {'id': 'shirokuma-dark', 'name': 'shirokuma Dark',
     'source': 'https://github.com/shirokuma89dev/KiCAD-Theme',
     'copyright': 'Copyright (c) 2023 しろくま胡瓜', 'license': 'MIT',
     'schematic': {'background': '#17171e', 'wire': '#3fbac0', 'bus': '#79be93', 'junction': '#3fbac0',
      'component_outline': '#d36b6e', 'component_body': 'rgba(86,61,73,0.169)', 'pin':
      '#d36b6e', 'pin_name': '#d19469', 'pin_number': '#d36b6e', 'reference': '#d36b6e',
      'value': '#b39fea', 'fields': '#bc8bea', 'label_local': 'rgba(156,192,106,0.922)',
      'label_global': 'rgba(156,192,106,0.922)', 'label_hier': 'rgba(156,192,106,0.922)',
      'sheet': '#b39fea', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name':
      'rgba(185,212,255,0.361)', 'sheet_filename': '#b39fea', 'sheet_label': '#c7885d',
      'no_connect': '#95dbdf', 'note': 'rgba(185,212,255,0.361)', 'worksheet':
      'rgba(185,212,255,0.361)'},
     'board': {'background': '#17171e', 'edge_cuts': 'rgba(168,192,109,0.678)', 'f_silks':
      'rgba(179,159,234,0.749)', 'b_silks': 'rgba(179,159,234,0.749)', 'f_mask':
      'rgba(216,100,255,0.4)', 'b_mask': 'rgba(2,255,238,0.4)', 'f_paste':
      'rgba(180,160,154,0.902)', 'b_paste': 'rgba(0,194,194,0.902)', 'f_crtyd':
      'rgba(211,133,137,0.369)', 'b_crtyd': 'rgba(94,148,211,0.322)', 'f_fab':
      'rgba(179,159,234,0.749)', 'b_fab': 'rgba(179,159,234,0.749)', 'pad_through_hole':
      'rgba(47,211,158,0.388)', 'via_through': 'rgba(236,236,236,0.678)', 'margin': '#c2a667',
      'dwgs_user': '#c2c2c2', 'cmts_user': '#5994dc', 'eco1_user': '#b4dbd2', 'eco2_user':
      '#d8c852', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4':
      '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8':
      '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': 'rgba(225,85,73,0.651)', 'b':
      'rgba(35,140,229,0.788)', 'in1': '#7fc87f', 'in2': '#ce7d2c', 'in3': '#4fcbcb', 'in4':
      '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7', 'in8': '#f2eda1', 'in9':
      '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6',
      'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18':
      '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7',
      'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27':
      '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30': '#f2eda1'}}},
    {'id': 'shirokuma-light', 'name': 'shirokuma Light',
     'source': 'https://github.com/shirokuma89dev/KiCAD-Theme',
     'copyright': 'Copyright (c) 2023 しろくま胡瓜', 'license': 'MIT',
     'schematic': {'background': '#ffffff', 'wire': '#38a5aa', 'bus': '#69a580', 'junction': '#38a5aa',
      'component_outline': '#944436', 'component_body': 'rgba(211,107,110,0.039)', 'pin':
      '#944436', 'pin_name': '#be7b3d', 'pin_number': '#944436', 'reference': '#944436',
      'value': '#8c7cb7', 'fields': '#840084', 'label_local': 'rgba(107,132,73,0.922)',
      'label_global': 'rgba(107,132,73,0.922)', 'label_hier': 'rgba(107,132,73,0.922)', 'sheet':
      '#8c7cb7', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': 'rgba(81,92,111,0.4)',
      'sheet_filename': '#8c7cb7', 'sheet_label': '#be7b3d', 'no_connect': '#38a5aa', 'note':
      'rgba(81,92,111,0.722)', 'worksheet': 'rgba(81,92,111,0.722)'},
     'board': {'background': '#ffffff', 'edge_cuts': 'rgba(174,181,66,0.761)', 'f_silks':
      'rgba(152,136,200,0.741)', 'b_silks': 'rgba(152,136,200,0.741)', 'f_mask':
      'rgba(216,100,255,0.4)', 'b_mask': 'rgba(2,255,238,0.4)', 'f_paste':
      'rgba(180,160,154,0.902)', 'b_paste': 'rgba(0,194,194,0.902)', 'f_crtyd':
      'rgba(211,133,137,0.369)', 'b_crtyd': 'rgba(94,148,211,0.322)', 'f_fab':
      'rgba(152,136,200,0.502)', 'b_fab': 'rgba(152,136,200,0.502)', 'pad_through_hole':
      'rgba(79,189,152,0.8)', 'via_through': 'rgba(212,212,212,0.831)', 'margin': '#c2a667',
      'dwgs_user': '#c2c2c2', 'cmts_user': '#5994dc', 'eco1_user': '#b4dbd2', 'eco2_user':
      '#d8c852', 'user_1': '#c2c2c2', 'user_2': '#5994dc', 'user_3': '#b4dbd2', 'user_4':
      '#d8c852', 'user_5': '#c2c2c2', 'user_6': '#5994dc', 'user_7': '#b4dbd2', 'user_8':
      '#d8c852', 'user_9': '#e8b2a7', 'copper': {'f': 'rgba(206,34,19,0.69)', 'b':
      'rgba(20,128,212,0.749)', 'in1': '#7fc87f', 'in2': '#ce7d2c', 'in3': '#4fcbcb', 'in4':
      '#db628b', 'in5': '#a7a5c6', 'in6': '#28ccd9', 'in7': '#e8b2a7', 'in8': '#f2eda1', 'in9':
      '#8dcb81', 'in10': '#ed7c33', 'in11': '#5bc3eb', 'in12': '#f76f8e', 'in13': '#a7a5c6',
      'in14': '#28ccd9', 'in15': '#e8b2a7', 'in16': '#f2eda1', 'in17': '#ed7c33', 'in18':
      '#5bc3eb', 'in19': '#f76f8e', 'in20': '#a7a5c6', 'in21': '#28ccd9', 'in22': '#e8b2a7',
      'in23': '#f2eda1', 'in24': '#ed7c33', 'in25': '#5bc3eb', 'in26': '#f76f8e', 'in27':
      '#a7a5c6', 'in28': '#28ccd9', 'in29': '#e8b2a7', 'in30': '#f2eda1'}}},
    {'id': 'dragonmux', 'name': 'dragonmux',
     'source': 'https://github.com/dragonmux/kicad-dragonmux-theme',
     'copyright': 'Rachel Mant', 'license': 'CC0-1.0',
     'schematic': {'background': '#212121', 'wire': '#00a000', 'bus': '#0060c0', 'junction': '#00a000',
      'component_outline': '#c00000', 'component_body': '#2c2c2c', 'pin': '#c00000', 'pin_name':
      '#c0c0c0', 'pin_number': '#c00000', 'reference': '#c0c0c0', 'value': '#c0c0c0', 'fields':
      '#8000a0', 'label_local': '#c0c0c0', 'label_global': '#00a0e0', 'label_hier': '#a0a000',
      'sheet': '#8000a0', 'sheet_background': '#2c2c2c', 'sheet_name': '#00aaff',
      'sheet_filename': '#c0c0c0', 'sheet_label': '#a0a000', 'no_connect': '#612be0', 'note':
      '#c0c0c0', 'worksheet': '#c00000'},
     'board': None},
    {'id': 'hartia', 'name': 'Hartia (Pen & Paper)',
     'source': 'https://gitlab.com/antto/kicad-themes',
     'copyright': 'Anton Savov', 'license': 'CC0-1.0',
     'schematic': {'background': '#e8e7e2', 'wire': '#5256d0', 'bus': '#176ddc', 'junction': '#4026c4',
      'component_outline': '#130040', 'component_body': '#dcdbe8', 'pin': '#010022', 'pin_name':
      '#15005e', 'pin_number': '#b4afbe', 'reference': '#8d7cb6', 'value': '#353dd0', 'fields':
      '#b277b2', 'label_local': '#b42d25', 'label_global': '#c03d3d', 'label_hier': '#c67d00',
      'sheet': '#7a0000', 'sheet_background': '#e2ded9', 'sheet_name': '#214bca',
      'sheet_filename': '#5ba46f', 'sheet_label': '#4c2188', 'no_connect': '#290eec', 'note':
      '#a4907e', 'worksheet': '#aa837a'},
     'board': None},
    {'id': 'nuova-elettronica', 'name': 'Nuova Elettronica',
     'source': 'https://github.com/tormyvancool/NuovaElettronica',
     'copyright': 'Tormy Van Cool', 'license': 'CC0-1.0',
     'schematic': {'background': '#f5f4ef', 'wire': '#000000', 'bus': '#000000', 'junction': '#000000',
      'component_outline': '#000000', 'component_body': '#d7ecff', 'pin': '#000000', 'pin_name':
      '#000000', 'pin_number': '#000000', 'reference': '#000000', 'value': '#000000', 'fields':
      '#840084', 'label_local': '#000000', 'label_global': '#86939f', 'label_hier': '#725600',
      'sheet': '#840000', 'sheet_background': 'rgba(255,255,255,0)', 'sheet_name': '#006464',
      'sheet_filename': '#725600', 'sheet_label': '#006464', 'no_connect': '#000084', 'note':
      '#0000c2', 'worksheet': '#840000'},
     'board': None},
    {'id': 'blue-green-dark', 'name': 'Blue-Green Dark',
     'source': 'https://github.com/pointhi/kicad-color-schemes',
     'copyright': 'pointhi/kicad-color-schemes', 'license': 'CC0-1.0',
     'schematic': None,
     'board': {'background': '#323232', 'edge_cuts': '#c2c200', 'f_silks': '#67968e', 'b_silks':
      '#968a67', 'f_mask': 'rgba(29,29,100,0.6)', 'b_mask': 'rgba(0,100,0,0.6)', 'f_paste':
      'rgba(132,70,74,0.4)', 'b_paste': 'rgba(132,88,44,0.6)', 'f_crtyd': '#5bdcdc', 'b_crtyd':
      '#b3be38', 'f_fab': '#3b99c8', 'b_fab': '#9cc843', 'pad_through_hole':
      'rgba(194,184,84,0.702)', 'via_through': 'rgba(160,160,160,0.8)', 'dwgs_user': '#d2d2d2',
      'cmts_user': '#843334', 'eco1_user': '#008400', 'eco2_user': '#c2c200', 'copper': {'f':
      'rgba(44,44,150,0.702)', 'b': 'rgba(44,150,62,0.702)', 'in1': 'rgba(110,50,170,0.702)',
      'in2': 'rgba(200,129,59,0.702)', 'in3': '#c20000', 'in4': '#008484', 'in5': '#008400',
      'in6': '#000084', 'in7': '#848484', 'in8': '#840084', 'in9': '#c2c2c2', 'in10': '#840084',
      'in11': '#840000', 'in12': '#848400', 'in13': '#c2c2c2', 'in14': '#000084', 'in15':
      '#008400', 'in16': '#840000', 'in17': '#c2c200', 'in18': '#c200c2', 'in19': '#c20000',
      'in20': '#008484', 'in21': '#008400', 'in22': '#000084', 'in23': '#848484', 'in24':
      '#840084', 'in25': '#c2c2c2', 'in26': '#840084', 'in27': '#840000', 'in28': '#848400',
      'in29': '#c2c2c2', 'in30': '#000084'}}},
]
