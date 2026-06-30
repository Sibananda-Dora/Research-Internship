import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[CDT ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0a0b0d',
          color: '#f3f4f6',
          fontFamily: 'Inter, sans-serif',
          padding: '40px'
        }}>
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '500px',
            textAlign: 'center'
          }}>
            <h2 style={{ color: '#ef4444', marginBottom: '12px', fontSize: '1.4rem' }}>
              Dashboard Error
            </h2>
            <p style={{ color: '#9ca3af', marginBottom: '16px', lineHeight: 1.5 }}>
              A component crashed while rendering. This usually happens when the backend
              returns data in an unexpected format.
            </p>
            <pre style={{
              background: 'rgba(0,0,0,0.3)',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '0.75rem',
              color: '#f59e0b',
              textAlign: 'left',
              overflow: 'auto',
              maxHeight: '120px',
              marginBottom: '16px'
            }}>
              {this.state.error?.toString()}
            </pre>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              style={{
                background: '#06b6d4',
                color: '#000',
                border: 'none',
                padding: '10px 24px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
