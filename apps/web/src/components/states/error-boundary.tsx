'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';

import { ErrorState } from '@/components/states/error-state';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Isola falhas de um widget específico (ex.: um card do dashboard) para que uma
 * exceção nele não derrube a página inteira. Precisa ser class component — React só
 * expõe `componentDidCatch`/`getDerivedStateFromError` nesse formato.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorState
          title={this.props.fallbackTitle ?? 'Este widget falhou'}
          message={this.state.error.message}
          onRetry={() => this.setState({ error: null })}
        />
      );
    }

    return this.props.children;
  }
}
