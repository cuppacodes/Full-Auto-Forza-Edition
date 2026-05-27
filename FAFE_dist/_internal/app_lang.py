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
    "support_btn": {
        "en":    "Support Me",
        "zh-tw": "支持我",
        "zh-cn": "支持我",
    },
    "tab_race": {
        "en":    "🏁  Race Auto",
        "zh-tw": "🏁  自動掛機刷技術點",
        "zh-cn": "🏁  自动挂机刷技术点",
    },
    "race_description": {
        "en":    "Before starting, enter the race you want to grind and stop at the Start Race screen.",
        "zh-tw": "開始之前請進入到想刷的地圖中並停在開始賽事的介面上。",
        "zh-cn": "开始之前请进入到想刷的地图中并停在开始赛事的界面上。",
    },
    "tab_mastery": {
        "en":    "⭐  Auto Unlock 22B",
        "zh-tw": "⭐  自動解鎖22B轉輪",
        "zh-cn": "⭐  自动解锁22B转轮",
    },
    "mastery_description": {
        "en":    "Before starting, make sure you are in the garage and the newest 22B in the top-left is brand new. The tool will snake downward and process each car one by one.",
        "zh-tw": "開始前請確保在車庫中並且左上角最新的是全新的22B，程式會用蛇行的方式往下開始一台一台處理。",
        "zh-cn": "开始前请确保在车库中并且左上角最新的是全新的22B，程序会用蛇行的方式往下开始一台一台处理。",
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
        "en":    "Would you like to download and install it now?",
        "zh-tw": "是否立即下載並安裝？",
        "zh-cn": "是否立即下载并安装？",
    },
    "update_yes": {
        "en":    "Update Now",
        "zh-tw": "立即更新",
        "zh-cn": "立即更新",
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
    "label_language": {
        "en":    "Language:",
        "zh-tw": "語言：",
        "zh-cn": "语言：",
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
        "en":    "Detection threshold:",
        "zh-tw": "偵測閾值：",
        "zh-cn": "检测阈值：",
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
        "en":    "Navigate your game to the same screen, then press CAPS LOCK to capture. A selection window will pop up — drag to select the area. If it doesn't appear, Alt-Tab to find it.",
        "zh-tw": "請將遊戲切換至相同畫面，然後按 CAPS LOCK 擷取。接著會彈出選取視窗讓你框選擷取範圍。若視窗未出現，請按 Alt-Tab 查看是否在背景。",
        "zh-cn": "请将游戏切换至相同画面，然后按 CAPS LOCK 截取。接着会弹出选取窗口让你框选截取范围。若窗口未出现，请按 Alt-Tab 查看是否在后台。",
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
        "en":    "Detection threshold",
        "zh-tw": "偵測閾值",
        "zh-cn": "检测阈值",
    },
    "setting_race_check_interval": {
        "en":    "Check interval (s)",
        "zh-tw": "檢測間隔（秒）",
        "zh-cn": "检测间隔（秒）",
    },
    "setting_race_post_key_wait": {
        "en":    "Key wait (s)",
        "zh-tw": "按鍵等待（秒）",
        "zh-cn": "按键等待（秒）",
    },
    "setting_mastery_threshold": {
        "en":    "Detection threshold",
        "zh-tw": "偵測閾值",
        "zh-cn": "检测阈值",
    },
    "setting_mastery_post_click_wait": {
        "en":    "Click wait (s)",
        "zh-tw": "點擊等待（秒）",
        "zh-cn": "点击等待（秒）",
    },
    "setting_mastery_post_key_wait": {
        "en":    "Key wait (s)",
        "zh-tw": "按鍵等待（秒）",
        "zh-cn": "按键等待（秒）",
    },

    # ── Run controls ──────────────────────────────────────────
    "btn_start": {
        "en":    "▶  Start",
        "zh-tw": "▶  開始",
        "zh-cn": "▶  开始",
    },
    "btn_stop": {
        "en":    "■  Stop",
        "zh-tw": "■  停止",
        "zh-cn": "■  停止",
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
    "mastery_tpl_ride_car": {
        "en":    "Ride This Car option",
        "zh-tw": "駕駛車輛選項",
        "zh-cn": "驾驶车辆选项",
    },
    "mastery_tpl_esc_hint": {
        "en":    "ESC hint at screen bottom",
        "zh-tw": "畫面底部 ESC 提示",
        "zh-cn": "画面底部 ESC 提示",
    },
    "mastery_tpl_upgrade_item": {
        "en":    "Upgrade & Tuning menu item",
        "zh-tw": "升級套件與調校選項",
        "zh-cn": "升级套件与调校选项",
    },
    "mastery_tpl_mastery_item": {
        "en":    "Car Mastery list item",
        "zh-tw": "車輛熟練度列表項目",
        "zh-cn": "车辆熟练度列表项目",
    },
    "mastery_tpl_anchor": {
        "en":    "Car Mastery screen header",
        "zh-tw": "車輛熟練度畫面標題",
        "zh-cn": "车辆熟练度画面标题",
    },
    "mastery_tpl_my_cars": {
        "en":    "My Cars button",
        "zh-tw": "我的車輛按鈕",
        "zh-cn": "我的车辆按钮",
    },
    "mastery_tpl_sort_recent": {
        "en":    "Recently Added sort option",
        "zh-tw": "最近新增排序選項",
        "zh-cn": "最近新增排序选项",
    },

    # ── Automation log messages ───────────────────────────────
    "log_template_loaded": {
        "en":    "  Template '{key}' loaded (scale {scale}x)",
        "zh-tw": "  樣本 '{key}' 已載入（縮放 {scale}x）",
        "zh-cn": "  模板 '{key}' 已加载（缩放 {scale}x）",
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
    "log_clicking": {
        "en":    "  Clicking {label} ({conf})",
        "zh-tw": "  點擊 {label}（{conf}）",
        "zh-cn": "  点击 {label}（{conf}）",
    },
    "log_not_found_retry": {
        "en":    "  {label} not found — retrying loop.",
        "zh-tw": "  找不到 {label} — 重試循環。",
        "zh-cn": "  找不到 {label} — 重试循环。",
    },
    "log_pressing_esc": {
        "en":    "  Pressing ESC...",
        "zh-tw": "  按下 ESC...",
        "zh-cn": "  按下 ESC...",
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
    "log_sort_pressing_x": {
        "en":    "  Pressing X — sort menu (attempt {n}/2)...",
        "zh-tw": "  按下 X — 排序選單（第 {n}/2 次）...",
        "zh-cn": "  按下 X — 排序菜单（第 {n}/2 次）...",
    },
    "log_sort_not_detected": {
        "en":    "  Sort menu not detected — retrying...",
        "zh-tw": "  未偵測到排序選單 — 重試中...",
        "zh-cn": "  未检测到排序菜单 — 重试中...",
    },
    "log_sort_not_found": {
        "en":    "  Sort menu not found after 2 attempts — continuing.",
        "zh-tw": "  兩次嘗試後仍未找到排序選單 — 繼續執行。",
        "zh-cn": "  两次尝试后仍未找到排序菜单 — 继续执行。",
    },
    "log_cutscene_continuing": {
        "en":    "  ESC hint not detected — continuing anyway.",
        "zh-tw": "  未偵測到 ESC 提示 — 仍繼續執行。",
        "zh-cn": "  未检测到 ESC 提示 — 仍继续执行。",
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
        "en":    "  Loop 1 — starting at row 1 col 1.",
        "zh-tw": "  第 1 循環 — 從第 1 列第 1 行開始。",
        "zh-cn": "  第 1 循环 — 从第 1 列第 1 行开始。",
    },
    "log_open_action_menu": {
        "en":    "  Pressing Enter to open action menu...",
        "zh-tw": "  按下 Enter 開啟動作選單...",
        "zh-cn": "  按下 Enter 打开动作菜单...",
    },
    "log_action_menu_not_found": {
        "en":    "  Action menu not detected — skipping.",
        "zh-tw": "  未偵測到動作選單 — 跳過。",
        "zh-cn": "  未检测到动作菜单 — 跳过。",
    },
    "log_buy_key": {
        "en":    "  Pressing [{key}]",
        "zh-tw": "  按下 [{key}]",
        "zh-cn": "  按下 [{key}]",
    },
    "log_template_set": {
        "en":    "  Template set: {res} → {folder}",
        "zh-tw": "  樣本組：{res} → {folder}",
        "zh-cn": "  模板组：{res} → {folder}",
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
    "tip_mastery_post_click_wait": {
        "en":    "How long to wait after each mouse click (in seconds).\nIncrease if the game misses clicks or menus open too slowly.",
        "zh-tw": "每次滑鼠點擊後的等待時間（秒）。\n若遊戲漏接點擊或選單開啟太慢，請增加此數值。",
        "zh-cn": "每次鼠标点击后的等待时间（秒）。\n若游戏漏接点击或菜单打开太慢，请增加此数值。",
    },
    "tip_mastery_post_key_wait": {
        "en":    "How long to wait after pressing a key before the next action (in seconds).\nIncrease if the game misses key presses.",
        "zh-tw": "按下按鍵後，等待下一個動作的時間（秒）。\n若遊戲漏接按鍵，請增加此數值。",
        "zh-cn": "按下按键后，等待下一个动作的时间（秒）。\n若游戏漏接按键，请增加此数值。",
    },
}


def t(string_key: str, lang: str, **kwargs) -> str:

    """Get a translated string. Falls back to English if missing."""
    entry = STRINGS.get(string_key, {})
    text  = entry.get(lang) or entry.get("en", f"[{string_key}]")
    if kwargs:
        text = text.format(**kwargs)
    return text
