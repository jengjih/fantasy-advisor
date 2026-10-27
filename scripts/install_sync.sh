#!/bin/zsh
# 安裝 Mac 端排程：每天 12:30、18:30、23:30 抓 NBA 數據並同步到 GitHub（給雲端 6:30 推播用）
# 同時移除舊的「Mac 6:30 推播」排程（已由 GitHub 雲端接手）
set -e
P="$HOME/Desktop/Claude Code實驗室/fantasy-advisor"
AGENTS="$HOME/Library/LaunchAgents"

# 1. 移除舊的本機推播排程
if [ -f "$AGENTS/com.lesunshine.notify.plist" ]; then
  launchctl unload "$AGENTS/com.lesunshine.notify.plist" 2>/dev/null || true
  rm "$AGENTS/com.lesunshine.notify.plist"
  echo "✓ 已移除舊的 Mac 6:30 推播排程"
fi

# 2. 安裝同步排程
cat > "$AGENTS/com.lesunshine.sync.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.lesunshine.sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.local/bin/uv</string><string>run</string><string>python</string><string>-W</string><string>ignore</string><string>sync.py</string>
  </array>
  <key>WorkingDirectory</key><string>$P</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Hour</key><integer>23</integer><key>Minute</key><integer>30</integer></dict>
  </array>
  <key>StandardOutPath</key><string>$P/logs/sync.log</string>
  <key>StandardErrorPath</key><string>$P/logs/sync.log</string>
</dict>
</plist>
PLIST
launchctl unload "$AGENTS/com.lesunshine.sync.plist" 2>/dev/null || true
launchctl load "$AGENTS/com.lesunshine.sync.plist"
echo "✓ 已安裝同步排程（每天 12:30、18:30、23:30）"

# 3. 立刻試跑一次
echo "… 試跑同步（約 30 秒）"
cd "$P" && "$HOME/.local/bin/uv" run python -W ignore sync.py
