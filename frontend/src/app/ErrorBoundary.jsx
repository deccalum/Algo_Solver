import React from "react";

export default class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, info: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        this.setState({ error, info });
        console.error("Unhandled error in component tree:", error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
                    <h2>Something went wrong</h2>
                    <pre style={{ whiteSpace: "pre-wrap", background: "#f8f8f8", padding: 12, borderRadius: 6 }}>
                        {String(this.state.error)}
                        {this.state.info?.componentStack ? "\n\n" + this.state.info.componentStack : ""}
                    </pre>
                    <p>
                        Try reloading the page. If the problem persists, open the devtools console and paste the error there.
                    </p>
                </div>
            );
        }

        return this.props.children;
    }
}
