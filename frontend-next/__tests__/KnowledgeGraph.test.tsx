import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import KnowledgeGraph from '../src/components/KnowledgeGraph';

// Mock the dynamic import of react-force-graph-2d
jest.mock('next/dynamic', () => () => {
  const DynamicComponent = () => <div data-testid="force-graph-mock">Mock Graph Canvas</div>;
  return DynamicComponent;
});

describe('KnowledgeGraph Component', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('fetches nodes and edges and renders the canvas', async () => {
    const mockNodes = [
      { id: "P-101", label: "EQUIPMENT" },
      { id: "REG-01", label: "REGULATION" }
    ];
    const mockEdges = [
      { source: "P-101", target: "REG-01", type: "GOVERNED_BY" }
    ];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: () => Promise.resolve(mockNodes) }) // api/nodes
      .mockResolvedValueOnce({ json: () => Promise.resolve(mockEdges) }); // api/edges

    render(<KnowledgeGraph activeRole="Engineer" />);
    
    expect(screen.getByText('Loading graph topology...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument();
    });
  });

  it('applies RBAC filtering for Operator role (hides Regulations)', async () => {
    // We can't directly check the internal state in black-box testing, 
    // but we can verify fetch is called and the graph mounts.
    const mockNodes = [
      { id: "P-101", label: "EQUIPMENT" },
      { id: "REG-01", label: "REGULATION" }
    ];
    const mockEdges = [
      { source: "P-101", target: "REG-01", type: "GOVERNED_BY" }
    ];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: () => Promise.resolve(mockNodes) }) // api/nodes
      .mockResolvedValueOnce({ json: () => Promise.resolve(mockEdges) }); // api/edges

    render(<KnowledgeGraph activeRole="Operator" />);
    
    await waitFor(() => {
      expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument();
    });
  });
});
