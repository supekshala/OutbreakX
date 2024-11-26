// src/App.tsx
import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import MapComponent from "./components/MapComponent";
import ChatComponent from "./components/chat";

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <header className="navbar">
          <div className="logo">OutbreakX</div>
          <nav>
            <ul className="nav-links">
              <li>
                <Link to="/">Home</Link>
              </li>
              <li>
                <Link to="/chat">Chat</Link>
              </li>
              <li>
                <Link to="/settings">Settings</Link>
              </li>
            </ul>
          </nav>
        </header>
        <section>
          <Routes>
            <Route path="/" element={<MapComponent />} />
            <Route path="/chat" element={<ChatComponent />} />
            {/* Add more routes as needed */}
          </Routes>
        </section>
      </div>
    </Router>
  );
};

export default App;
