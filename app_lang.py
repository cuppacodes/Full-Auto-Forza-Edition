# ============================================================
#  app_lang.py — GUI string translations for forza_app
#  Separate from lang.py (which serves the terminal scripts)
#  Supports: English (en), Traditional Chinese (zh-tw),
#             Simplified Chinese (zh-cn)
# ============================================================

STRINGS = {

    # ── Window / tabs ─────────────────────────────────────────
    "app_title": {
        "en":    "FAFE",
        "zh-tw": "FAFE",
        "zh-cn": "FAFE",
    },
    "support_thanks": {
        "en":    "If FAFE saves you time, a small tip helps keep it maintained. Thank you!",
        "zh-tw": "如果 FAFE 為你節省了時間，小額贊助能幫助它持續維護。感謝你！",
        "zh-cn": "如果 FAFE 为你节省了时间，小额赞助能帮助它持续维护。感谢你！",
    },
    "support_jkopay": {
        "en":    "街口支付 (JKOPAY) — scan to tip",
        "zh-tw": "街口支付（掃碼贊助）",
        "zh-cn": "街口支付（扫码赞助）",
    },
    "support_btn": {
        "en":    "Support Me",
        "zh-tw": "支持我",
        "zh-cn": "支持我",
    },
    "label_accent_color": {
        "en":    "Accent color",
        "zh-tw": "強調色",
        "zh-cn": "强调色",
    },
    "tab_race": {
        "en":    "🏁  Race Auto",
        "zh-tw": "🏁  自動掛機刷技術點",
        "zh-cn": "🏁  自动挂机刷技术点",
    },
    "race_description": {
        "en":    "Before starting, enter the race you want to grind and stop at the Start Race screen. The Start Race and race-end (Restart) screens are detected; the rest is timed.",
        "zh-tw": "開始之前請進入到想刷的地圖中並停在開始賽事的介面上。本模式會偵測開始賽事與賽事結束（重新開始）畫面，其餘以定時操作。",
        "zh-cn": "开始之前请进入到想刷的地图中并停在开始赛事的界面上。本模式会检测开始赛事与赛事结束（重新开始）画面，其余以定时操作。",
    },
    "tab_mastery": {
        "en":    "⭐  Auto Unlock 22B",
        "zh-tw": "⭐  自動解鎖22B轉輪",
        "zh-cn": "⭐  自动解锁22B转轮",
    },
    "mastery_description": {
        "en":    "Before starting, make sure you are in your My Home garage (not the Horizon Festival map menu) and the newest 22B in the top-left is brand new. The tool will snake downward and process each car one by one.",
        "zh-tw": "開始前請確保在我的住所裡的車庫（非大世界選單），並且左上角最新的是全新的22B，程式會用蛇行的方式往下開始一台一台處理。",
        "zh-cn": "开始前请确保在我的住所里的车库（非大世界选单），并且左上角最新的是全新的22B，程序会用蛇行的方式往下开始一台一台处理。",
    },

    "tab_buy": {
        "en":    "🛒  Auto Buy 22B-STi",
        "zh-tw": "🛒  自動購買22B-STi",
        "zh-cn": "🛒  自动购买22B-STi",
    },
    "buy_description": {
        "en":    "Before starting, navigate to: Menu → Journal → Master Explorer → Car Collection → find the 22B-STi and click on it. Leave the game on that screen, then press Start.",
        "zh-tw": "開始前，請先在遊戲中依序進入：選單 → 收藏日記 → 探索大師 → 車輛收藏 → 找到 22B-STi 並點擊。停在該畫面後再按下開始。",
        "zh-cn": "开始前，请先在游戏中依次进入：菜单 → 收藏日记 → 探索大师 → 车辆收藏 → 找到 22B-STi 并点击。停在该画面后再按下开始。",
    },
    "status_starting_buy": {
        "en":    "Starting Auto Buy...",
        "zh-tw": "正在啟動自動購買...",
        "zh-cn": "正在启动自动购买...",
    },
    "buy_running": {
        "en":    "Auto Buy started.",
        "zh-tw": "自動購買已啟動。",
        "zh-cn": "自动购买已启动。",
    },
    "buy_loop": {
        "en":    "Loop",
        "zh-tw": "循環",
        "zh-cn": "循环",
    },

    # ── Delete Cars ───────────────────────────────────────────
    "tab_delete": {
        "en":    "🗑️  Delete Used Cars",
        "zh-tw": "🗑️  刪除已使用車輛",
        "zh-cn": "🗑️  删除已使用车辆",
    },
    # Main-header page titles (emoji-free; the sidebar nav reuses the tab_* labels)
    "page_title_race": {
        "en":    "Race Auto",
        "zh-tw": "自動掛機刷技術點",
        "zh-cn": "自动挂机刷技术点",
    },
    "page_title_mastery": {
        "en":    "Auto Unlock 22B",
        "zh-tw": "自動解鎖22B轉輪",
        "zh-cn": "自动解锁22B转轮",
    },
    "page_title_buy": {
        "en":    "Auto Buy 22B-STi",
        "zh-tw": "自動購買22B-STi",
        "zh-cn": "自动购买22B-STi",
    },
    "page_title_delete": {
        "en":    "Delete Used Cars",
        "zh-tw": "刪除已使用車輛",
        "zh-cn": "删除已使用车辆",
    },
    "delete_description": {
        "en":    "Automatically deletes cars one by one. For each car: opens action menu → navigates down 4 times → confirms → navigates down once → confirms deletion.\n\nBefore starting, go to your garage and select the oldest car you want to start deleting from (bottom-right of the grid). The tool deletes from oldest to newest.\n\nIf there is a car you don't want to delete in the path, press Stop to cancel.",
        "zh-tw": "自動逐一刪除車輛。每輛車的操作：開啟動作選單 → 下鍵 ×4 → 確認 → 下鍵 ×1 → 確認刪除。\n\n使用前停在車庫裡你想批量刪除中最舊的那台（最右下角的），程式會由舊到最新去刪除。\n\n如果路徑上有不想刪除的車請記得按停止鍵取消。",
        "zh-cn": "自动逐一删除车辆。每辆车的操作：打开动作菜单 → 下键 ×4 → 确认 → 下键 ×1 → 确认删除。\n\n使用前停在车库里你想批量删除中最旧的那台（最右下角的），程序会由旧到最新去删除。\n\n如果路径上有不想删除的车请记得按停止键取消。",
    },
    "status_starting_delete": {
        "en":    "Starting Delete Used Cars...",
        "zh-tw": "正在啟動刪除車輛...",
        "zh-cn": "正在启动删除车辆...",
    },
    "log_delete_started": {
        "en":    "Auto Delete started.",
        "zh-tw": "自動刪除已啟動。",
        "zh-cn": "自动删除已启动。",
    },
    "log_delete_started_count": {
        "en":    "Auto Delete started — will delete {n} cars.",
        "zh-tw": "自動刪除已啟動 — 將刪除 {n} 輛車。",
        "zh-cn": "自动删除已启动 — 将删除 {n} 辆车。",
    },
    "log_delete_limit_reached": {
        "en":    "Reached target of {n} cars deleted. Stopping.",
        "zh-tw": "已完成目標 {n} 輛，自動停止。",
        "zh-cn": "已完成目标 {n} 辆，自动停止。",
    },
    "delete_count_label": {
        "en":    "Number of cars to delete:",
        "zh-tw": "要刪除的車輛數量：",
        "zh-cn": "要删除的车辆数量：",
    },
    "delete_count_hint": {
        "en":    "(0 = unlimited)",
        "zh-tw": "（0 = 無限循環）",
        "zh-cn": "（0 = 无限循环）",
    },
    "buy_count_label": {
        "en":    "Number of cars to buy:",
        "zh-tw": "要購買的車輛數量：",
        "zh-cn": "要购买的车辆数量：",
    },
    "log_buy_limit_reached": {
        "en":    "Reached target of {n} purchases. Stopping.",
        "zh-tw": "已完成目標 {n} 次購買，自動停止。",
        "zh-cn": "已完成目标 {n} 次购买，自动停止。",
    },
    "mastery_count_label": {
        "en":    "Number of cars to process:",
        "zh-tw": "要處理的車輛數量：",
        "zh-cn": "要处理的车辆数量：",
    },
    "race_count_label": {
        "en":    "Number of races to run:",
        "zh-tw": "要跑的場數：",
        "zh-cn": "要跑的场数：",
    },
    "log_mastery_started_count": {
        "en":    "Auto Mastery started — will process {n} cars.",
        "zh-tw": "自動熟練度已啟動 — 將處理 {n} 輛車。",
        "zh-cn": "自动熟练度已启动 — 将处理 {n} 辆车。",
    },
    "log_mastery_limit_reached": {
        "en":    "Reached target of {n} cars. Stopping.",
        "zh-tw": "已完成目標 {n} 輛，自動停止。",
        "zh-cn": "已完成目标 {n} 辆，自动停止。",
    },
    "log_race_started_count": {
        "en":    "Race Auto started — will run {n} races.",
        "zh-tw": "自動跑圖已啟動 — 將跑 {n} 場。",
        "zh-cn": "自动跑图已启动 — 将跑 {n} 场。",
    },
    "log_race_limit_reached": {
        "en":    "Reached target of {n} races. Stopping.",
        "zh-tw": "已完成目標 {n} 場，自動停止。",
        "zh-cn": "已完成目标 {n} 场，自动停止。",
    },
    "log_delete_stopped": {
        "en":    "Auto Delete stopped.",
        "zh-tw": "自動刪除已停止。",
        "zh-cn": "自动删除已停止。",
    },
    "delete_loop": {
        "en":    "Car",
        "zh-tw": "車輛",
        "zh-cn": "车辆",
    },

    # ── Updater ───────────────────────────────────────────────
    "update_title": {
        "en":    "Update Available",
        "zh-tw": "有新版本",
        "zh-cn": "有新版本",
    },
    "update_available": {
        "en":    "A new version is available: {tag}",
        "zh-tw": "發現新版本：{tag}",
        "zh-cn": "发现新版本：{tag}",
    },
    "update_prompt": {
        "en":    "Open the download page to get the latest version?",
        "zh-tw": "是否開啟下載頁面取得最新版本？",
        "zh-cn": "是否打开下载页面获取最新版本？",
    },
    "update_yes": {
        "en":    "Open download page",
        "zh-tw": "開啟下載頁面",
        "zh-cn": "打开下载页面",
    },
    "update_no": {
        "en":    "Later",
        "zh-tw": "稍後再說",
        "zh-cn": "稍后再说",
    },

    # ── Top bar ───────────────────────────────────────────────
    "settings_window_title": {
        "en":    "Settings",
        "zh-tw": "設定",
        "zh-cn": "设置",
    },
    "settings_back": {
        "en":    "Back",
        "zh-tw": "返回",
        "zh-cn": "返回",
    },
    "settings_race_section": {
        "en":    "Race Auto",
        "zh-tw": "自動掛機刷技術點",
        "zh-cn": "自动挂机刷技术点",
    },
    "settings_mastery_section": {
        "en":    "Auto Unlock 22B",
        "zh-tw": "自動解鎖22B轉輪",
        "zh-cn": "自动解锁22B转轮",
    },
    "settings_buy_section": {
        "en":    "Auto Buy 22B-STi",
        "zh-tw": "自動購買22B-STi",
        "zh-cn": "自动购买22B-STi",
    },
    "settings_delete_section": {
        "en":    "Delete Used Cars",
        "zh-tw": "刪除已使用車輛",
        "zh-cn": "删除已使用车辆",
    },
    "settings_appearance_section": {
        "en":    "Appearance",
        "zh-tw": "外觀",
        "zh-cn": "外观",
    },
    "settings_shortcuts_section": {
        "en":    "Shortcuts",
        "zh-tw": "快捷鍵",
        "zh-cn": "快捷键",
    },
    "label_theme": {
        "en":    "Theme:",
        "zh-tw": "主題：",
        "zh-cn": "主题：",
    },
    "label_theme_preset": {
        "en":    "Theme",
        "zh-tw": "主題",
        "zh-cn": "主题",
    },
    "label_language": {
        "en":    "Language:",
        "zh-tw": "語言：",
        "zh-cn": "语言：",
    },
    "label_ui_scale": {
        "en":    "UI scale:",
        "zh-tw": "介面縮放：",
        "zh-cn": "界面缩放：",
    },
    "setting_game_lang": {
        "en":    "Game menu language:",
        "zh-tw": "遊戲選單語言：",
        "zh-cn": "游戏菜单语言：",
    },
    "game_lang_auto": {
        "en":    "Auto (follow app)",
        "zh-tw": "自動（跟隨介面）",
        "zh-cn": "自动（跟随界面）",
    },
    "setting_overlay": {
        "en":    "Game status overlay:",
        "zh-tw": "遊戲狀態浮層：",
        "zh-cn": "游戏状态浮层：",
    },
    "overlay_indicator": {
        "en":    "Overlay",
        "zh-tw": "浮層",
        "zh-cn": "浮层",
    },
    "ov_func_race": {
        "en": "Race", "zh-tw": "賽事", "zh-cn": "赛事",
    },
    "ov_func_mastery": {
        "en": "Mastery", "zh-tw": "熟練度", "zh-cn": "熟练度",
    },
    "ov_func_buy": {
        "en": "Buy", "zh-tw": "購買", "zh-cn": "购买",
    },
    "ov_func_delete": {
        "en": "Delete", "zh-tw": "刪除", "zh-cn": "删除",
    },
    "overlay_hint_stop": {
        "en":    "■  Press {key} to stop",
        "zh-tw": "■  按 {key} 停止",
        "zh-cn": "■  按 {key} 停止",
    },
    "overlay_hint_start": {
        "en":    "▶  Press {key} to start",
        "zh-tw": "▶  按 {key} 開始",
        "zh-cn": "▶  按 {key} 开始",
    },
    "scale_auto": {
        "en":    "Auto",
        "zh-tw": "自動",
        "zh-cn": "自动",
    },
    "theme_system": {
        "en":    "System",
        "zh-tw": "系統",
        "zh-cn": "系统",
    },
    "theme_light": {
        "en":    "Light",
        "zh-tw": "淺色",
        "zh-cn": "浅色",
    },
    "theme_dark": {
        "en":    "Dark",
        "zh-tw": "深色",
        "zh-cn": "深色",
    },

    # ── Setup panel ───────────────────────────────────────────
    "setup_header": {
        "en":    "▶  Setup & Templates",
        "zh-tw": "▶  設定與樣本",
        "zh-cn": "▶  设置与模板",
    },
    "setup_header_open": {
        "en":    "▼  Setup & Templates",
        "zh-tw": "▼  設定與樣本",
        "zh-cn": "▼  设置与模板",
    },
    "label_threshold": {
        "en":    "Minimum required similarity:",
        "zh-tw": "最低所需相似度：",
        "zh-cn": "最低所需相似度：",
    },
    "label_resolution": {
        "en":    "Template set:",
        "zh-tw": "樣本組：",
        "zh-cn": "模板组：",
    },
    "res_1080p": {
        "en":    "1080p (Built-in)",
        "zh-tw": "1080p（內建）",
        "zh-cn": "1080p（内置）",
    },
    "res_1440p": {
        "en":    "1440p (Built-in)",
        "zh-tw": "1440p（內建）",
        "zh-cn": "1440p（内置）",
    },
    "res_2160p": {
        "en":    "4K (Built-in)",
        "zh-tw": "4K（內建）",
        "zh-cn": "4K（内置）",
    },
    "res_custom": {
        "en":    "Custom (Capture your own)",
        "zh-tw": "自定義（自行擷取）",
        "zh-cn": "自定义（自行截取）",
    },
    "label_monitor": {
        "en":    "Game monitor:",
        "zh-tw": "遊戲螢幕：",
        "zh-cn": "游戏显示器：",
    },
    "monitor_primary_tag": {
        "en":    "(Primary)",
        "zh-tw": "（主螢幕）",
        "zh-cn": "（主显示器）",
    },
    "label_templates": {
        "en":    "Templates (press CAPS LOCK to capture each):",
        "zh-tw": "樣本（按 CAPS LOCK 逐一擷取）：",
        "zh-cn": "模板（按 CAPS LOCK 逐一截取）：",
    },
    "label_nodes": {
        "en":    "Node positions (6 mastery nodes)",
        "zh-tw": "節點位置（6 個熟練度節點）",
        "zh-cn": "节点位置（6 个熟练度节点）",
    },
    "btn_start_capture": {
        "en":    "Start Capture Session",
        "zh-tw": "開始擷取作業",
        "zh-cn": "开始截取作业",
    },
    "btn_stop_capture": {
        "en":    "Stop Session",
        "zh-tw": "停止作業",
        "zh-cn": "停止作业",
    },
    "btn_recapture": {
        "en":    "Retake",
        "zh-tw": "重新擷取",
        "zh-cn": "重新截取",
    },
    "capture_instruction": {
        "en":    "Navigate your game to the same screen, then press CAPS LOCK to capture. Drag to select the area, then press ENTER to confirm. Press ESC at any time to cancel. If the selection window doesn't appear, Alt-Tab to find it.",
        "zh-tw": "請將遊戲切換至相同畫面，然後按 CAPS LOCK 擷取。拖曳框選範圍後按 ENTER 確認。隨時按 ESC 可取消。若視窗未出現，請按 Alt-Tab 查看是否在背景。",
        "zh-cn": "请将游戏切换至相同画面，然后按 CAPS LOCK 截取。拖曳框选范围后按 ENTER 确认。随时按 ESC 可取消。若窗口未出现，请按 Alt-Tab 查看是否在后台。",
    },
    "capture_nodes_instruction": {
        "en":    "Get to the Mastery screen, press CAPS LOCK to screenshot then click 6 nodes.",
        "zh-tw": "進入熟練度畫面，按 CAPS LOCK 截圖後點擊 6 個節點。",
        "zh-cn": "进入熟练度画面，按 CAPS LOCK 截图后点击 6 个节点。",
    },
    "capture_cancelled": {
        "en":    "Capture {reason} — press CAPS LOCK to retry.",
        "zh-tw": "擷取{reason} — 按 CAPS LOCK 重試。",
        "zh-cn": "截取{reason} — 按 CAPS LOCK 重试。",
    },
    "setup_complete": {
        "en":    "Setup complete.",
        "zh-tw": "設定完成。",
        "zh-cn": "设置完成。",
    },
    "setup_in_progress": {
        "en":    "Setup in progress.",
        "zh-tw": "設定進行中。",
        "zh-cn": "设置进行中。",
    },
    "all_templates_done": {
        "en":    "All templates already captured.",
        "zh-tw": "所有樣本已擷取完成。",
        "zh-cn": "所有模板已截取完成。",
    },
    "capturing_label": {
        "en":    "Capturing: {label}",
        "zh-tw": "擷取中：{label}",
        "zh-cn": "截取中：{label}",
    },
    "template_saved": {
        "en":    "  Template '{key}' saved.",
        "zh-tw": "  樣本 '{key}' 已儲存。",
        "zh-cn": "  模板 '{key}' 已保存。",
    },
    "nodes_saved": {
        "en":    "  Node positions saved.",
        "zh-tw": "  節點位置已儲存。",
        "zh-cn": "  节点位置已保存。",
    },

    # ── Advanced settings ─────────────────────────────────────
    "settings_header": {
        "en":    "▶  Advanced Settings",
        "zh-tw": "▶  進階設定",
        "zh-cn": "▶  高级设置",
    },
    "settings_header_open": {
        "en":    "▼  Advanced Settings",
        "zh-tw": "▼  進階設定",
        "zh-cn": "▼  高级设置",
    },
    "setting_race_threshold": {
        "en":    "Minimum required similarity",
        "zh-tw": "最低所需相似度",
        "zh-cn": "最低所需相似度",
    },
    "setting_race_check_interval": {
        "en":    "Check interval (s)",
        "zh-tw": "檢測間隔（秒）",
        "zh-cn": "检测间隔（秒）",
    },
    "setting_race_post_key_wait": {
        "en":    "Trigger to input delay (s)",
        "zh-tw": "觸發與開始輸入之間的間隔（秒）",
        "zh-cn": "触发与开始输入之间的间隔（秒）",
    },
    "setting_mastery_threshold": {
        "en":    "Minimum required similarity",
        "zh-tw": "最低所需相似度",
        "zh-cn": "最低所需相似度",
    },
    "setting_mastery_node_click_wait": {
        "en":    "Mastery node click interval (s)",
        "zh-tw": "點擊熟練度間隔（秒）",
        "zh-cn": "点击熟练度间隔（秒）",
    },
    "setting_buy_post_key_wait": {
        "en":    "Key interval (s)",
        "zh-tw": "按鍵間隔（秒）",
        "zh-cn": "按键间隔（秒）",
    },
    "setting_delete_post_key_wait": {
        "en":    "Key interval (s)",
        "zh-tw": "按鍵間隔（秒）",
        "zh-cn": "按键间隔（秒）",
    },

    # ── Run controls ──────────────────────────────────────────
    "btn_start": {
        "en":    "Start",
        "zh-tw": "開始",
        "zh-cn": "开始",
    },
    "btn_stop": {
        "en":    "Stop",
        "zh-tw": "停止",
        "zh-cn": "停止",
    },

    # ── Status messages ───────────────────────────────────────
    "shortcut_toggle": {
        "en":    "{key} to start / stop",
        "zh-tw": "{key} 啟動 / 停止",
        "zh-cn": "{key} 启动 / 停止",
    },
    "shortcut_capture": {
        "en":    "Press {key} to capture | Y = save | N = redo",
        "zh-tw": "按 {key} 擷取 | Y = 儲存 | N = 重拍",
        "zh-cn": "按 {key} 截取 | Y = 保存 | N = 重拍",
    },
    "setting_toggle_key": {
        "en":    "Start / Stop key",
        "zh-tw": "啟動 / 停止鍵",
        "zh-cn": "启动 / 停止键",
    },
    "setting_capture_key": {
        "en":    "Capture key",
        "zh-tw": "擷取鍵",
        "zh-cn": "截取键",
    },
    "setting_report_key": {
        "en":    "Bug report key",
        "zh-tw": "錯誤回報鍵",
        "zh-cn": "错误回报键",
    },
    "setting_overlay_key": {
        "en":    "Overlay toggle key",
        "zh-tw": "浮層切換鍵",
        "zh-cn": "浮层切换键",
    },
    "report_started": {
        "en":    "🐞 Bug report started — capturing screenshot, logs & system info...",
        "zh-tw": "🐞 已開始產生錯誤回報 — 擷取截圖、日誌與系統資訊中…",
        "zh-cn": "🐞 已开始生成错误回报 — 截取截图、日志与系统信息中…",
    },
    "report_generating": {
        "en":    "Generating bug report — capturing screenshot & log...",
        "zh-tw": "正在產生錯誤回報 — 擷取截圖與日誌中…",
        "zh-cn": "正在生成错误回报 — 截取截图与日志中…",
    },
    "report_specs": {
        "en":    "Collecting system info (DxDiag, may take ~30s)...",
        "zh-tw": "正在收集系統資訊（DxDiag，約需 30 秒）…",
        "zh-cn": "正在收集系统信息（DxDiag，约需 30 秒）…",
    },
    "report_saved": {
        "en":    "✅ Bug report complete — saved to: {path}",
        "zh-tw": "✅ 錯誤回報已完成 — 儲存於：{path}",
        "zh-cn": "✅ 错误回报已完成 — 保存于：{path}",
    },
    "report_privacy": {
        "en":    "Note: this bundle includes your settings and system info (DxDiag — includes your Windows username & hardware). Fine to share for support; review before posting publicly.",
        "zh-tw": "注意：此回報包含你的設定與系統資訊（DxDiag，含 Windows 使用者名稱與硬體）。提供給支援沒問題，公開分享前請先檢視。",
        "zh-cn": "注意：此回报包含你的设置与系统信息（DxDiag，含 Windows 用户名与硬件）。提供给支持没问题，公开分享前请先查看。",
    },
    "report_help_btn": {
        "en":    "Report a Bug",
        "zh-tw": "回報錯誤",
        "zh-cn": "回报错误",
    },
    "report_help_title": {
        "en":    "How to Report a Bug",
        "zh-tw": "如何回報錯誤",
        "zh-cn": "如何回报错误",
    },
    "report_help_intro": {
        "en":    "Found a problem? Send us a one-click diagnostic report — just follow these steps:",
        "zh-tw": "遇到問題嗎？只要依照以下步驟，就能一鍵傳送診斷回報：",
        "zh-cn": "遇到问题吗？只要按照以下步骤，就能一键发送诊断回报：",
    },
    "report_help_step1": {
        "en":    "Run the script (Race / Mastery / etc.) and let it run until the problem happens — i.e. it gets stuck or stops working.",
        "zh-tw": "執行腳本（賽事／熟練度等），讓它持續運作直到發生問題（卡住或停止運作）。",
        "zh-cn": "运行脚本（赛事／熟练度等），让它持续运行直到发生问题（卡住或停止运行）。",
    },
    "report_help_step2": {
        "en":    "When it fails, STAY on that exact game screen — don't alt-tab, click away, or close anything.",
        "zh-tw": "發生問題時，請停留在當下的遊戲畫面 — 不要切換視窗、點擊其他地方或關閉任何東西。",
        "zh-cn": "发生问题时，请停留在当下的游戏画面 — 不要切换窗口、点击其他地方或关闭任何东西。",
    },
    "report_help_step3": {
        "en":    "With that failing screen still showing, press {key}.",
        "zh-tw": "在問題畫面仍顯示的狀態下，按下 {key}。",
        "zh-cn": "在问题画面仍显示的状态下，按下 {key}。",
    },
    "report_help_step4": {
        "en":    "FAFE saves a report (screenshot of that screen + log + system info) and opens the folder automatically.",
        "zh-tw": "FAFE 會自動儲存回報（該畫面的截圖＋日誌＋系統資訊）並開啟資料夾。",
        "zh-cn": "FAFE 会自动保存回报（该画面的截图＋日志＋系统信息）并打开文件夹。",
    },
    "report_help_step5": {
        "en":    "Upload the FAFE_report_….zip to our Discord, and tell us your screen resolution and which tab failed.",
        "zh-tw": "將 FAFE_report_….zip 上傳到我們的 Discord，並告訴我們你的螢幕解析度與發生問題的分頁。",
        "zh-cn": "将 FAFE_report_….zip 上传到我们的 Discord，并告诉我们你的屏幕分辨率与发生问题的标签页。",
    },
    "report_help_discord": {
        "en":    "Join our Discord",
        "zh-tw": "加入我們的 Discord",
        "zh-cn": "加入我们的 Discord",
    },
    "shortcut_press_any_key": {
        "en":    "Press any key...",
        "zh-tw": "請按下任意鍵...",
        "zh-cn": "请按下任意键...",
    },
    "startup_game_not_focused": {
        "en":    "  WARNING: Forza Horizon 6 is not the active window.\n  Please switch to the game before the countdown ends.",
        "zh-tw": "  警告：Forza Horizon 6 並非目前使用中的視窗。\n  請在倒數結束前切換至遊戲。",
        "zh-cn": "  警告：Forza Horizon 6 并非当前活动窗口。\n  请在倒数结束前切换至游戏。",
    },
    "startup_game_focused": {
        "en":    "  Forza Horizon 6 detected.",
        "zh-tw": "  已偵測到 Forza Horizon 6。",
        "zh-cn": "  已检测到 Forza Horizon 6。",
    },
    "startup_switch_to_game": {
        "en":    "  Switch to your game now!",
        "zh-tw": "  請立即切換至遊戲！",
        "zh-cn": "  请立即切换至游戏！",
    },
    "startup_countdown": {
        "en":    "  Starting in {i}...",
        "zh-tw": "  {i} 秒後開始...",
        "zh-cn": "  {i} 秒后开始...",
    },
    "startup_running": {
        "en":    "  Running!",
        "zh-tw": "  開始執行！",
        "zh-cn": "  开始执行！",
    },
    "log_placeholder": {

        "en":    "Automation log will appear here when running...",
        "zh-tw": "執行後，自動化紀錄將顯示於此...",
        "zh-cn": "运行后，自动化记录将显示于此...",
    },
    "status_ready": {
        "en":    "Ready",
        "zh-tw": "就緒",
        "zh-cn": "就绪",
    },
    "status_starting_race": {
        "en":    "Starting race automation...",
        "zh-tw": "正在啟動自動競速...",
        "zh-cn": "正在启动自动竞速...",
    },
    "status_starting_mastery": {
        "en":    "Starting Mastery Lite...",
        "zh-tw": "正在啟動熟練度精簡版...",
        "zh-cn": "正在启动熟练度精简版...",
    },
    "status_stopping": {
        "en":    "Stopping...",
        "zh-tw": "停止中...",
        "zh-cn": "停止中...",
    },
    "status_stopped": {
        "en":    "Stopped",
        "zh-tw": "已停止",
        "zh-cn": "已停止",
    },
    "status_setup_incomplete": {
        "en":    "Setup incomplete — missing templates",
        "zh-tw": "設定未完成 — 缺少樣本",
        "zh-cn": "设置未完成 — 缺少模板",
    },

    # ── Race template labels ──────────────────────────────────
    "race_tpl_start_menu": {
        "en":    "Start Race menu",
        "zh-tw": "開始比賽選單",
        "zh-cn": "开始比赛菜单",
    },
    "race_tpl_racing": {
        "en":    "Race active (HUD / speedometer)",
        "zh-tw": "比賽進行中（HUD / 速度表）",
        "zh-cn": "比赛进行中（HUD / 速度表）",
    },
    "race_tpl_restart_menu": {
        "en":    "Restart Race menu",
        "zh-tw": "重新開始比賽選單",
        "zh-cn": "重新开始比赛菜单",
    },
    "race_tpl_confirm": {
        "en":    "Confirmation dialog",
        "zh-tw": "確認對話框",
        "zh-cn": "确认对话框",
    },

    # ── Mastery template labels ───────────────────────────────

    # ── Automation log messages ───────────────────────────────
    "log_template_loaded": {
        "en":    "  Template '{key}' loaded.",
        "zh-tw": "  樣本 '{key}' 已載入。",
        "zh-cn": "  模板 '{key}' 已加载。",
    },
    "log_nodes_loaded": {
        "en":    "  {n} node positions loaded.",
        "zh-tw": "  已載入 {n} 個節點位置。",
        "zh-cn": "  已加载 {n} 个节点位置。",
    },
    "log_template_missing": {
        "en":    "  ERROR: Template '{key}' not found. Run setup first.",
        "zh-tw": "  錯誤：找不到樣本 '{key}'。請先執行設定。",
        "zh-cn": "  错误：找不到模板 '{key}'。请先运行设置。",
    },
    "log_nodes_missing": {
        "en":    "  ERROR: Node positions not found. Run setup first.",
        "zh-tw": "  錯誤：找不到節點位置。請先執行設定。",
        "zh-cn": "  错误：找不到节点位置。请先运行设置。",
    },
    "log_race_started": {
        "en":    "Race automation started.",
        "zh-tw": "自動競速已啟動。",
        "zh-cn": "自动竞速已启动。",
    },
    "log_race_stopped": {
        "en":    "Race automation stopped.",
        "zh-tw": "自動競速已停止。",
        "zh-cn": "自动竞速已停止。",
    },
    "log_mastery_started": {
        "en":    "Auto Unlock 22B started.",
        "zh-tw": "自動解鎖22B轉輪已啟動。",
        "zh-cn": "自动解锁22B转轮已启动。",
    },
    "log_mastery_stopped": {
        "en":    "Auto Unlock 22B stopped.",
        "zh-tw": "自動解鎖22B轉輪已停止。",
        "zh-cn": "自动解锁22B转轮已停止。",
    },
    "log_loop": {
        "en":    "\n-- Loop #{n} --",
        "zh-tw": "\n-- 第 {n} 圈 --",
        "zh-cn": "\n-- 第 {n} 圈 --",
    },
    "log_car": {
        "en":    "\n-- Car #{n} --",
        "zh-tw": "\n-- 第 {n} 輛 --",
        "zh-cn": "\n-- 第 {n} 辆 --",
    },
    "log_detected": {
        "en":    "  {label} detected ({conf})",
        "zh-tw": "  偵測到 {label}（{conf}）",
        "zh-cn": "  检测到 {label}（{conf}）",
    },
    "log_timed_out": {
        "en":    "  {label} timed out after {t}s",
        "zh-tw": "  {label} 於 {t} 秒後逾時",
        "zh-cn": "  {label} 于 {t} 秒后超时",
    },
    "log_warn_not_detected": {
        "en":    "⚠ WARNING: '{label}' not detected after 10s. If not detecting, try dragging the threshold slider to the left. You may also need to recapture this template. If the game ignores all input (car won't move / clicks do nothing), run FAFE as administrator.",
        "zh-tw": "⚠ 警告：'{label}' 超過 10 秒未偵測到。若持續無法偵測，請將閾值滑桿向左拖動。也可以嘗試重新擷取此樣本。若遊戲完全不接受輸入（車子不動／點擊無效），請以系統管理員身分執行 FAFE。",
        "zh-cn": "⚠ 警告：'{label}' 超过 10 秒未检测到。若持续无法检测,请将阈值滑块向左拖动。也可以尝试重新截取此模板。若游戏完全不接受输入（车子不动／点击无效），请以管理员身份运行 FAFE。",
    },
    "log_timed_out_retry": {
        "en":    "  Timed out — retrying.",
        "zh-tw": "  逾時 — 重試中。",
        "zh-cn": "  超时 — 重试中。",
    },
    "log_pressing": {
        "en":    "  Pressing {key} [{label}]",
        "zh-tw": "  按下 {key}【{label}】",
        "zh-cn": "  按下 {key}【{label}】",
    },
    "log_race_wait_start": {
        "en":    "  Race starting — waiting before holding W...",
        "zh-tw": "  賽事開始中 — 按住 W 前先等待...",
        "zh-cn": "  赛事开始中 — 按住 W 前先等待...",
    },
    "log_holding_w": {
        "en":    "  Holding W — waiting for race to end...",
        "zh-tw": "  按住 W — 等待比賽結束...",
        "zh-cn": "  按住 W — 等待比赛结束...",
    },
    "log_released_w": {
        "en":    "  Released W — race over.",
        "zh-tw": "  釋放 W — 比賽結束。",
        "zh-cn": "  释放 W — 比赛结束。",
    },
    "log_race_end_timeout": {
        "en":    "  Race end not detected after 1h — releasing W.",
        "zh-tw": "  1 小時後仍未偵測到比賽結束 — 釋放 W。",
        "zh-cn": "  1 小时后仍未检测到比赛结束 — 释放 W。",
    },
    "log_not_found_retry": {
        "en":    "  {label} not found — retrying loop.",
        "zh-tw": "  找不到 {label} — 重試循環。",
        "zh-cn": "  找不到 {label} — 重试循环。",
    },
    "log_esc_x2": {
        "en":    "  Pressing ESC x2 to return...",
        "zh-tw": "  按下 ESC 兩次返回...",
        "zh-cn": "  按下 ESC 两次返回...",
    },
    "log_clicking_nodes": {
        "en":    "  Clicking {n} mastery nodes...",
        "zh-tw": "  點擊 {n} 個熟練度節點...",
        "zh-cn": "  点击 {n} 个熟练度节点...",
    },
    "log_node": {
        "en":    "    Node {i}/{n} at ({x},{y})",
        "zh-tw": "    節點 {i}/{n} 位於 ({x},{y})",
        "zh-cn": "    节点 {i}/{n} 位于 ({x},{y})",
    },
    "log_loop": {
        "en":    "Loop",
        "zh-tw": "循環",
        "zh-cn": "循环",
    },
    "log_navigating": {
        "en":    "  Navigating: {keys}",
        "zh-tw": "  導航中：{keys}",
        "zh-cn": "  导航中：{keys}",
    },
    "log_loop1_start": {
        "en":    "  Starting at row {row} — no navigation needed.",
        "zh-tw": "  從第 {row} 排開始 — 無需移動。",
        "zh-cn": "  从第 {row} 排开始 — 无需移动。",
    },
    "log_open_action_menu": {
        "en":    "  Pressing Enter to open action menu...",
        "zh-tw": "  按下 Enter 開啟動作選單...",
        "zh-cn": "  按下 Enter 打开动作菜单...",
    },
    "log_esc_back": {
        "en":    "  Pressing ESC ×2 to exit...",
        "zh-tw": "  按下 ESC ×2 返回...",
        "zh-cn": "  按下 ESC ×2 返回...",
    },
    "log_buy_key": {
        "en":    "  Pressing [{key}]",
        "zh-tw": "  按下 [{key}]",
        "zh-cn": "  按下 [{key}]",
    },
    "status_user_select": {
        "en":    "Please select a new 22B-STI and open the action menu.",
        "zh-tw": "請選擇一輛新的 22B-STI 並開啟動作選單。",
        "zh-cn": "请选择一辆新的 22B-STI 并打开动作菜单。",
    },
    "status_waiting_action_menu": {
        "en":    "Waiting for action menu (Ride This Car)...",
        "zh-tw": "等待動作選單（駕駛車輛）...",
        "zh-cn": "等待动作菜单（驾驶车辆）...",
    },
    "status_racing": {
        "en":    "Racing — holding W...",
        "zh-tw": "比賽中 — 按住 W...",
        "zh-cn": "比赛中 — 按住 W...",
    },
    "status_waiting_for": {
        "en":    "Waiting for {label}...",
        "zh-tw": "等待 {label}...",
        "zh-cn": "等待 {label}...",
    },
    # ── Setting tooltips ─────────────────────────────────────────
    "tip_race_threshold": {
        "en":    "How closely the screen must match the template to count as detected.\nHigher = stricter. Lower = more lenient but may cause false detections.",
        "zh-tw": "畫面與樣本的相符程度，達到此值才視為偵測成功。\n數值越高越嚴格，越低則越寬鬆但可能誤判。",
        "zh-cn": "画面与模板的匹配程度，达到此值才视为检测成功。\n数值越高越严格，越低则越宽松但可能误判。",
    },
    "tip_race_check_interval": {
        "en":    "How often the screen is checked for each state (in seconds).\nLower = faster response but uses more CPU.",
        "zh-tw": "每次偵測畫面狀態的間隔時間（秒）。\n數值越低反應越快，但 CPU 使用率越高。",
        "zh-cn": "每次检测画面状态的间隔时间（秒）。\n数值越低响应越快，但 CPU 占用越高。",
    },
    "tip_race_post_key_wait": {
        "en":    "How long to wait after pressing a key before the next action (in seconds).\nIncrease if the game misses key presses.",
        "zh-tw": "按下按鍵後，等待下一個動作的時間（秒）。\n若遊戲漏接按鍵，請增加此數值。",
        "zh-cn": "按下按键后，等待下一个动作的时间（秒）。\n若游戏漏接按键，请增加此数值。",
    },
    "tip_mastery_threshold": {
        "en":    "How closely the screen must match the template to count as detected.\nHigher = stricter. Lower = more lenient but may cause false detections.",
        "zh-tw": "畫面與樣本的相符程度，達到此值才視為偵測成功。\n數值越高越嚴格，越低則越寬鬆但可能誤判。",
        "zh-cn": "画面与模板的匹配程度，达到此值才视为检测成功。\n数值越高越严格，越低则越宽松但可能误判。",
    },
    "tip_mastery_node_click_wait": {
        "en":    "How long to wait after each mastery node click (in seconds).\nIncrease if the game misses node clicks.",
        "zh-tw": "每次點擊熟練度節點後的等待時間（秒）。\n若遊戲漏接節點點擊，請增加此數值。",
        "zh-cn": "每次点击熟练度节点后的等待时间（秒）。\n若游戏漏接节点点击，请增加此数值。",
    },
    "tip_buy_post_key_wait": {
        "en":    "How long to wait between each key press during purchase (in seconds).",
        "zh-tw": "每次購買按鍵之間的等待時間（秒）。",
        "zh-cn": "每次购买按键之间的等待时间（秒）。",
    },
    "tip_delete_post_key_wait": {
        "en":    "How long to wait between each key press during deletion (in seconds).",
        "zh-tw": "每次刪除按鍵之間的等待時間（秒）。",
        "zh-cn": "每次删除按键之间的等待时间（秒）。",
    },

    "mastery_start_row_label": {
        "en":    "Start from row",
        "zh-tw": "從第幾排開始",
        "zh-cn": "从第几排开始",
    },
    "mastery_start_row_hint": {
        "en":    "(which row is your first car on?)",
        "zh-tw": "（你的第一台車在哪一排？）",
        "zh-cn": "（你的第一台车在哪一排？）",
    },

    # ── Mastery mode toggle (detect / keys) ───────────────────
    "log_mkeys_ride": {
        "en":    "Pressing Enter — Ride This Car",
        "zh-tw": "按下 Enter — 駕駛這輛車",
        "zh-cn": "按下 Enter — 驾驶这辆车",
    },
    "log_mkeys_cutscene": {
        "en":    "Waiting for the cutscene, then pressing ESC...",
        "zh-tw": "等待過場動畫後按 ESC…",
        "zh-cn": "等待过场动画后按 ESC…",
    },
    "log_mkeys_upgrade": {
        "en":    "Pressing Down + Enter — Upgrade & Tuning",
        "zh-tw": "按下 ↓ + Enter — 升級與調校",
        "zh-cn": "按下 ↓ + Enter — 升级与调校",
    },
    "log_mkeys_mastery": {
        "en":    "Pressing Down ×7 + Enter — Car Mastery",
        "zh-tw": "按下 ↓ ×7 + Enter — 車輛熟練度",
        "zh-cn": "按下 ↓ ×7 + Enter — 车辆熟练度",
    },
    "log_mkeys_wait_mastery": {
        "en":    "Waiting for the Mastery screen...",
        "zh-tw": "等待熟練度畫面…",
        "zh-cn": "等待熟练度画面…",
    },
    "log_mkeys_mycars": {
        "en":    "Pressing Up + Enter — My Cars",
        "zh-tw": "按下 ↑ + Enter — 我的車輛",
        "zh-cn": "按下 ↑ + Enter — 我的车辆",
    },
    "log_mkeys_sort": {
        "en":    "Pressing X + Down ×6 + Enter — sort by Recently Added",
        "zh-tw": "按下 X + ↓ ×6 + Enter — 依最近新增排序",
        "zh-cn": "按下 X + ↓ ×6 + Enter — 按最近添加排序",
    },
}


def t(string_key: str, lang: str, **kwargs) -> str:

    """Get a translated string. Falls back to English if missing."""
    entry = STRINGS.get(string_key, {})
    text  = entry.get(lang) or entry.get("en", f"[{string_key}]")
    if kwargs:
        text = text.format(**kwargs)
    return text
