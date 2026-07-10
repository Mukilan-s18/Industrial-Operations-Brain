import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInterface from '../src/components/ChatInterface';

// Mock the SpeechRecognition API that ChatInterface looks for
beforeAll(() => {
  (window as any).SpeechRecognition = jest.fn().mockImplementation(() => ({
    start: jest.fn(),
    stop: jest.fn(),
  }));
});

describe('ChatInterface Component', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = jest.fn();
    // Mock localStorage for token fetching
    Storage.prototype.getItem = jest.fn(() => 'mock_token');
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('renders correctly and accepts input', () => {
    render(<ChatInterface activeRole="Engineer" />);
    
    expect(screen.getByText('Interactive RCA Chat')).toBeInTheDocument();
    
    const input = screen.getByPlaceholderText('Ask as Engineer...');
    fireEvent.change(input, { target: { value: 'Why is P-101 vibrating?' } });
    expect(input).toHaveValue('Why is P-101 vibrating?');
  });

  it('submits a message and handles SSE stream response', async () => {
    // Mock the fetch stream response
    const mockStreamData = [
      'data: {"node": "check_sensors"}\n\n',
      'data: {"answer": "The vibration is high due to bearing wear.", "contradiction_detected": false, "faithfulness_score": 0.95, "action_taken": "CREATE_SAP_WO", "action_result": "Created WO 123"}\n\n'
    ];

    let readCallCount = 0;
    const mockReader = {
      read: jest.fn().mockImplementation(() => {
        if (readCallCount < mockStreamData.length) {
          const value = new TextEncoder().encode(mockStreamData[readCallCount]);
          readCallCount++;
          return Promise.resolve({ done: false, value });
        }
        return Promise.resolve({ done: true });
      }),
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader,
      },
    });

    render(<ChatInterface activeRole="Engineer" />);
    
    const input = screen.getByPlaceholderText('Ask as Engineer...');
    fireEvent.change(input, { target: { value: 'Why is P-101 vibrating?' } });
    
    const submitBtn = document.querySelector('button[type="submit"]') as HTMLButtonElement;
    
    // Using act for fireEvent that causes state updates
    fireEvent.click(submitBtn);

    // Verify user message appeared
    await waitFor(() => {
      expect(screen.getByText('Why is P-101 vibrating?')).toBeInTheDocument();
    });

    // Wait for stream to finish processing
    await waitFor(() => {
      expect(screen.getByText('The vibration is high due to bearing wear.')).toBeInTheDocument();
    });
    
    // Verify action block appeared
    expect(screen.getByText('CREATE_SAP_WO')).toBeInTheDocument();
    expect(screen.getByText('Created WO 123')).toBeInTheDocument();
  });
});
