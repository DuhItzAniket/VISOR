#!/usr/bin/env bash
# Run inside the clean-room image with Docker networking disabled.
set -euo pipefail

test "$(printf '%s\n' /sys/class/net/*)" = /sys/class/net/lo
if command -v python >/dev/null || command -v python3 >/dev/null; then
    echo "Unexpected system Python executable in the clean-room image" >&2
    exit 1
fi
test ! -e /opt/visor
test ! -e /usr/share/doc/visor
if dpkg-query -W visor >/dev/null 2>&1; then
    echo "VISOR is already registered in the clean-room image" >&2
    exit 1
fi

printf 'Network interfaces: lo\n'
cat /etc/os-release
sha256sum /fixture/visor.deb /fixture/portable.tar.gz
printf 'Package declarations:\n'
dpkg-deb --field /fixture/visor.deb Package Version Architecture Depends
printf 'Preinstalled OS and display packages:\n'
dpkg-query -W -f='${binary:Package}\t${Version}\n'

workdir=$(mktemp -d)
chown nobody:nogroup "$workdir"
install -d -m 700 -o nobody -g nogroup "$workdir/runtime"

smoke() {
    local executable=$1 report=$2
    runuser -u nobody -- /usr/bin/env -i \
        HOME="$workdir" XDG_RUNTIME_DIR="$workdir/runtime" PATH=/usr/bin:/bin LANG=C.UTF-8 \
        QT_QPA_PLATFORM=xcb QT_XCB_GL_INTEGRATION=none QT_OPENGL=software \
        CUDA_VISIBLE_DEVICES=-1 OPENCV_OPENCL_RUNTIME=disabled \
        /usr/bin/xvfb-run -a -s '-screen 0 1280x800x24 -nolisten tcp -extension GLX' \
        /usr/bin/env PATH=/nonexistent "$executable" --smoke-check "$report"
    cat "$report"
    grep -Eq '"qt_platform":[[:space:]]*"xcb"' "$report"
    grep -Eq '"success":[[:space:]]*true' "$report"
}

dpkg --install /fixture/visor.deb
dpkg-query -L visor | grep -Fx /usr/share/applications/org.visor.desktop.desktop
test -f /usr/share/doc/visor/system-notices/manifest.json
smoke /opt/visor/VISOR "$workdir/installed-smoke.json"
dpkg --purge visor
test ! -e /opt/visor
test ! -e /usr/share/applications/org.visor.desktop.desktop
test ! -e /usr/share/doc/visor

mkdir "$workdir/portable"
tar -xzf /fixture/portable.tar.gz -C "$workdir/portable"
test -f "$workdir/portable/VISOR-system-notices/manifest.json"
smoke "$workdir/portable/VISOR/VISOR" "$workdir/portable-smoke.json"
printf 'Clean Ubuntu installed and portable X11 checks passed.\n'
