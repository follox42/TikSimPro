#!/bin/bash
# Script pour démarrer un environnement graphique accessible via navigateur
# Usage: ./start_vnc.sh [start|stop|status]

VNC_PORT=5900
NOVNC_PORT=6080
DISPLAY_NUM=99
RESOLUTION="1920x1080x24"
VNC_PASSWORD="tiksimpro"  # Change ce mot de passe!

start_vnc() {
    echo "🚀 Démarrage de l'environnement graphique..."

    # Arrêter les instances existantes
    stop_vnc 2>/dev/null

    # Démarrer Xvfb (écran virtuel)
    Xvfb :${DISPLAY_NUM} -screen 0 ${RESOLUTION} &
    sleep 2

    # Démarrer un gestionnaire de fenêtres léger
    DISPLAY=:${DISPLAY_NUM} fluxbox &
    sleep 1

    # Démarrer x11vnc
    x11vnc -display :${DISPLAY_NUM} -forever -shared -rfbport ${VNC_PORT} -passwd ${VNC_PASSWORD} -bg

    # Démarrer noVNC (accès web)
    websockify --web=/usr/share/novnc/ ${NOVNC_PORT} localhost:${VNC_PORT} &

    echo ""
    echo "✅ Environnement graphique démarré!"
    echo ""
    echo "📺 Accès via navigateur web:"
    echo "   http://$(hostname -I | awk '{print $1}'):${NOVNC_PORT}/vnc.html"
    echo "   ou via Tailscale: http://<IP_TAILSCALE>:${NOVNC_PORT}/vnc.html"
    echo ""
    echo "🔑 Mot de passe VNC: ${VNC_PASSWORD}"
    echo ""
    echo "Pour lancer TikSimPro avec cet écran:"
    echo "   export DISPLAY=:${DISPLAY_NUM}"
    echo "   python main.py"
}

stop_vnc() {
    echo "🛑 Arrêt de l'environnement graphique..."
    pkill -f "Xvfb :${DISPLAY_NUM}" 2>/dev/null
    pkill -f "x11vnc.*:${DISPLAY_NUM}" 2>/dev/null
    pkill -f "websockify.*${NOVNC_PORT}" 2>/dev/null
    pkill -f fluxbox 2>/dev/null
    echo "✅ Arrêté"
}

status_vnc() {
    echo "📊 Status:"
    if pgrep -f "Xvfb :${DISPLAY_NUM}" > /dev/null; then
        echo "  ✅ Xvfb: Running"
    else
        echo "  ❌ Xvfb: Stopped"
    fi

    if pgrep -f "x11vnc" > /dev/null; then
        echo "  ✅ x11vnc: Running"
    else
        echo "  ❌ x11vnc: Stopped"
    fi

    if pgrep -f "websockify.*${NOVNC_PORT}" > /dev/null; then
        echo "  ✅ noVNC: Running on port ${NOVNC_PORT}"
    else
        echo "  ❌ noVNC: Stopped"
    fi
}

case "${1:-start}" in
    start)
        start_vnc
        ;;
    stop)
        stop_vnc
        ;;
    status)
        status_vnc
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
