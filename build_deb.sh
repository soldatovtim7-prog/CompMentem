#!/usr/bin/env bash
# build_deb.sh — сборка .deb для CompMentem
set -e

APP_NAME="compmentem"
APP_VERSION="1.3.0"
ARCH="amd64"
MAINTAINER="soldatovtim7-prog"
DESCRIPTION="Terminal command manager with embedded PTY terminal"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "═══ 1. PyInstaller ═══"
rm -rf build dist *.spec
pyinstaller \
  --onefile \
  --windowed \
  --name "$APP_NAME" \
  --collect-all customtkinter \
  --collect-all pyte \
  --hidden-import=pty \
  --hidden-import=fcntl \
  --hidden-import=termios \
  --hidden-import=struct \
  --hidden-import=errno \
  --hidden-import=select \
  "$APP_NAME.py"

if [ ! -f "dist/$APP_NAME" ]; then
  echo "❌ PyInstaller не создал бинарник"
  exit 1
fi
echo "✅ Бинарник: $(du -h dist/$APP_NAME | cut -f1)"

echo "═══ 2. Структура .deb ═══"
PKG="pkg"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN"
mkdir -p "$PKG/usr/bin"
mkdir -p "$PKG/usr/share/applications"
mkdir -p "$PKG/usr/share/icons/hicolor/scalable/apps"

cp "dist/$APP_NAME" "$PKG/usr/bin/$APP_NAME"
chmod +x "$PKG/usr/bin/$APP_NAME"

# .desktop
cat > "$PKG/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=CompMentem
Comment=$DESCRIPTION
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;TerminalEmulator;
Keywords=terminal;command;manager;
EOF

# иконка (если есть)
if [ -f "compmentem.svg" ]; then
  cp compmentem.svg "$PKG/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"
elif [ -f "compmentem.png" ]; then
  cp compmentem.png "$PKG/usr/share/icons/hicolor/scalable/apps/$APP_NAME.png"
else
  echo "⚠ Иконка не найдена — сделаю заглушку"
  cat > "$PKG/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="20" fill="#0097a7"/>
  <text x="64" y="82" font-family="monospace" font-size="48" font-weight="bold"
        fill="#ffffff" text-anchor="middle">&gt;_</text>
</svg>
SVG
fi

echo "═══ 3. DEBIAN/control ═══"
cat > "$PKG/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $APP_VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 CompMentem — GUI-менеджер терминальных команд.
 Хранит команды, категории, теги, историю запусков.
 Встроенный терминал на настоящем PTY (vim, htop, readline).
EOF

echo "═══ 4. Сборка .deb ═══"
OUTPUT="${APP_NAME}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --root-owner-group --build "$PKG" "$OUTPUT"

echo ""
echo "✅ Готово: $OUTPUT"
echo "   Размер: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "Установка:  sudo apt install ./$OUTPUT"
echo "Удаление:   sudo apt remove $APP_NAME"