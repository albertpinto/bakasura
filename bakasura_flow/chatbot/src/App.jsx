import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Chatbot from './components/Chatbot';
import PoemGenerator from './components/PoemGenerator';
import NewsGenerator from './components/NewsGenerator';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-red-800 p-4">
          <div className="container mx-auto flex gap-4">
            <Link to="/" className="text-white hover:text-gray-200">Chat</Link>
            <Link to="/poem" className="text-white hover:text-gray-200">Poem Generator</Link>
            <Link to="/news" className="text-white hover:text-gray-200">News Generator</Link>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Chatbot />} />
          <Route path="/poem" element={<PoemGenerator />} />
          <Route path="/news" element={<NewsGenerator />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
