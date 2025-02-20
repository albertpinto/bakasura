import React, { useEffect, useState, useRef } from "react";
import { ChatOpenAI } from "langchain/chat_models/openai";
import { BufferMemory } from "langchain/memory";
import { ConversationChain } from "langchain/chains";
import { SerpAPI } from "langchain/tools";

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [randomName, setRandomName] = useState(null);
  const [chatSummary, setChatSummary] = useState("");
  const [showSummary, setShowSummary] = useState(false);

  const chain = useRef(
    new ConversationChain({
      llm: new ChatOpenAI({
        openAIApiKey: process.env.REACT_APP_OPENAI_API_KEY,
        temperature: 0,
        model: "gpt-3.5-turbo", // Updated model name
      }),
      memory: new BufferMemory({returnMessages: true, memoryKey: "history"}),
      tools: [
        new SerpAPI(process.env.REACT_APP_SERPAPI_API_KEY, {
          location: "Austin,Texas,United States",
          hl: "en",
          gl: "us",
        }),
      ],
    })
  ).current;

  const nameList = [
    "Alice",
    "Bob",
    "Charlie",
    "David",
    "Emma",
    "Frank",
    "Heather",
    "Ivan",
    "John",
  ];

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * nameList.length);
    setRandomName(nameList[randomIndex]);
  }, []);

  useEffect(() => {
    if (randomName) {
      const initializeChat = async () => {
        const response = await chain.call({
          input: `Hi! I'm ${process.env.REACT_APP_USER_ID}. Your name is: ${randomName}`,
        });
        const initialResponse = response.response;
        setMessages([{ text: initialResponse, type: "bot" }]);
      };
      initializeChat();
    }
  }, [randomName]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = async () => {
    if (inputValue.trim() !== "") {
      const botResponse = await chain.call({ input: inputValue });

      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: inputValue, type: "user" },
          { text: botResponse.response, type: "bot" },
        ]);
      }, 1000);
      setInputValue("");
    }
  };

  const handleClear = () => {
    setMessages([]);
    setInputValue("");
    chain.memory.clear();
    setRandomName(nameList[Math.floor(Math.random() * nameList.length)]);
    setChatSummary("");
    setShowSummary(false);
  };

  const handleSummarize = async () => {
    const response = await chain.call({ input: "Summarize the chat" });
    const summary = response.response;
    setChatSummary(summary);
    if (showSummary) setShowSummary(false); // Hide the summary text area
    else setShowSummary(true); // Show the summary text area
  };
  return (
    <div className="w-auto h-auto border border-gray-600 flex flex-col justify-between">
      <div className="flex p-4 border-t border-gray-600">
        <h3 className="text-xl font-bold">AI Chat</h3>
      </div>
      <div className="p-4 overflow-y-auto">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-2 p-2 rounded ${
              message.type === "user"
                ? "bg-gray-200 ml-auto"
                : "bg-sky-500/100 shadow-lg shadow-sky-500/50"
            }`}
          >
            {message.text}
          </div>
        ))}
      </div>
      <div className="flex p-4 border-t border-gray-600">
        <input
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="flex-1 p-2 border border-gray-600 rounded mr-2"
        />
        <button
          onClick={handleClear}
          className="px-4 py-1 bg-sky-500/100  shadow-lg shadow-sky-500/100 rounded-full"
        >
          Clear
        </button>
        <button
          onClick={handleSend}
          className="px-4 py-1 bg-sky-500/100 shadow-lg shadow-sky-500/100 rounded-full"
        >
          Send
        </button>
        <button
          onClick={handleSummarize}
          className="px-4 py-1 bg-sky-500/100 shadow-lg shadow-sky-500/100 rounded-full"
        >
          {showSummary ? "Hide Summary" : "Summary"}
        </button>
      </div>
      {showSummary && (
        <div className="p-4 border-t border-gray-600">
          <h3 className="text-xl font-bold">Summary</h3>
          <div className="pt-4 flex justify-between">
            <textarea
              value={chatSummary}
              readOnly
              placeholder=""
              className="w-full bg-sky-500/100 shadow-red-500/50 rounded text-black-800 p-2"
              rows="4"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBot;
