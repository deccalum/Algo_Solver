import React, { useEffect, useState } from "react";
import { Plus, Trash2, Upload } from "lucide-react";
import footerStyles from "../styles/Footer.module.css";
import statusStyles from "../styles/SystemPanel.module.css";

export default function Footer() {
    const [dbStatus, setDbStatus] = useState("unknown");
    const [terminalOpen, setTerminalOpen] = useState(false);
    const [terminalText] = useState("$ engine status\nidle\n$ db ping\nok\n$ docker ps\nsolver-container · running");

    useEffect(() => {
        let mounted = true;
        // try a lightweight ping to backend DB status endpoint; fall back to unknown
        fetch("/api/db/status")
            .then((r) => r.json())
            .then((json) => {
                if (!mounted) return;
                setDbStatus(json?.status === "ok" ? "connected" : "down");
            })
            .catch(() => {
                if (!mounted) return;
                setDbStatus("unknown");
            });

        return () => {
            mounted = false;
        };
    }, []);

    function handleOpenTerminal() {
        // dispatch an app-level event so host can open a real terminal if available
        window.dispatchEvent(new CustomEvent("openTerminal"));
        setTerminalOpen((v) => !v);
    }

    return (
        <>
            <footer className={footerStyles.bottomPanel}>
                <div className={footerStyles.leftCluster}>
                    <span className={`${statusStyles.statusItem}`}>
                        <span className={`${statusStyles.statusDot} ${statusStyles.running}`} />
                        Docker: Running
                    </span>
                    <span className={`${statusStyles.statusItem}`}>
                        <span className={`${statusStyles.statusDot} ${dbStatus === "connected" ? statusStyles.running : dbStatus === "down" ? statusStyles.down : statusStyles.idle}`} />
                        DB: {dbStatus}
                    </span>
                    <span className={`${statusStyles.statusItem}`}>
                        <span className={`${statusStyles.statusDot} ${statusStyles.idle}`} />
                        Engine: Idle
                    </span>
                    <span className={statusStyles.statusItem}>Solver: 12ms</span>
                </div>

                <div className={footerStyles.statusScroller}>
                    autosave:on · export:ready · snapshot:queued · logs:0 · solver_idle · distribution_synced
                </div>

                <div className={footerStyles.rightCluster}>
                    <button className={footerStyles.terminalCaret} onClick={handleOpenTerminal} title="Toggle terminal">^
                    </button>
                    <button title="Add preset" className={footerStyles.iconButton}>
                        <Plus size={14} />
                    </button>
                    <button title="Delete preset" className={footerStyles.iconButton}>
                        <Trash2 size={14} />
                    </button>
                    <button title="Upload preset" className={footerStyles.iconButton}>
                        <Upload size={14} />
                    </button>
                </div>
            </footer>

            {terminalOpen && (
                <section className={footerStyles.terminalPopup}>
                    <div className={footerStyles.terminalTitle}>Terminal</div>
                    <div className={footerStyles.terminalBody}>{terminalText}</div>
                </section>
            )}
        </>
    );
}
