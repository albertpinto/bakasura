// ===============================
// Frontend: essayStore.js
// ===============================
import { create } from 'zustand';

const useEssayStore = create((set, get) => ({
  // Base state
  program: '',
  student: '',
  college: '',
  resumeFile: null,
  selectedModel: 'o1-mini',
  essayType: 'college essay',
  customPrompt: '',
  messages: [],
  isStreaming: false,
  error: null,
  pdfContent: null,

  // Basic setters
  setProgram: (program) => set({ program }),
  setStudent: (student) => set({ student }),
  setCollege: (college) => set({ college }),
  setResumeFile: (resumeFile) => set({ resumeFile }),
  setSelectedModel: (selectedModel) => set({ selectedModel }),
  
  // Essay type handling
  setEssayType: (essayType) => set((state) => ({
    essayType,
    ...(essayType !== 'college essay' && {
      program: '',
      college: ''
    }),
    ...(essayType !== 'custom_prompt' && {
      customPrompt: ''
    })
  })),
  
  // Custom prompt handling
  setCustomPrompt: (customPrompt) => set({ customPrompt }),
  
  // Message and status handling
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  setError: (error) => set({ error }),
  setPdfContent: (pdfContent) => set({ pdfContent }),

  // Field validation
  validateFields: () => {
    const state = get();
    const baseRequired = state.student && state.resumeFile && state.selectedModel;
    
    switch (state.essayType) {
      case 'college essay':
        return baseRequired && state.program && state.college;
      case 'personal_statement':
        return baseRequired;
      case 'custom_prompt':
        return baseRequired && state.customPrompt;
      default:
        return false;
    }
  },

  // Reset all state
  clearAll: () => set({
    program: '',
    student: '',
    college: '',
    resumeFile: null,
    selectedModel: 'o1-mini',
    essayType: 'college essay',
    customPrompt: '',
    messages: [],
    isStreaming: false,
    error: null,
    pdfContent: null,
  }),
}));

export default useEssayStore;
