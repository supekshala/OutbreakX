import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

jest.mock('./components/MapComponent', () => () => <div>Map placeholder</div>);

test('renders outbreak console heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/outbreakx anomaly detection console/i);
  expect(headingElement).toBeInTheDocument();
});
