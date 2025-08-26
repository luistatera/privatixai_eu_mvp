# PrivatixAI - Fully Offline Personal AI Assistant

[![Privacy First](https://img.shields.io/badge/Privacy-First-green.svg)](https://github.com/privatixai/privatixai)

[![Offline Only](https://img.shields.io/badge/Offline-Only-blue.svg)](https://github.com/privatixai/privatixai)

[![Cross Platform](https://img.shields.io/badge/Platform-Cross-orange.svg)](https://github.com/privatixai/privatixai)


A privacy-first, fully offline AI Chatbot assistant for personal knowledge management. Built with Electron, React, FastAPI, and local AI models.

**Visit our official website: [https://privatixai.eu/](https://privatixai.eu/)**

## 🎯 Core Mission

**100% Local Processing • Zero Cloud Dependencies • Complete Data Sovereignty**

PrivatixAI Chatbot ensures your personal data never leaves your device while providing powerful AI assistance for document analysis, transcription, and knowledge management.

## ✨ Features

### 🔒 Privacy & Security
- **Offline Documents**: All docs are locally
- **No Cloud Storage**: Zero external storage
- **Data Sovereignty**: Your data stays on your device, a fraction is sent to EU server (with restrict GDPR policies in place)

### 🧠 AI Capabilities
- **Local LLM**: Powered by Ollama (Mistral, Llama, etc.)
- **Speech-to-Text**: Whisper-based transcription
- **Document Analysis**: PDF, DOCX processing
- **Vector Search**: ChromaDB-powered memory

### 📁 File Support
- **File Support (PDF, DOCX)**
- **Video YouTube URL**

### 🖥️ User Experience
- **Single App**: One download, zero configuration
- **Cross-Platform**: macOS, (Next version with Windows and Linux)
- **Desktop Native**: Full Electron experience
- **Non-Technical Friendly**: No terminal required

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           PrivatixAI Desktop            │
├─────────────────┬───────────────────────┤
│  Frontend       │      Backend          │
│  (React)        │     (FastAPI)         │
│                 │                       │
│  • Chat UI      │  • LLM Service        │
│  • File Upload  │  • Vector Store       │
│  • Memory View  │  • Transcription      │
│  • Settings     │  • (License Manager — v1.1) │
└─────────────────┴───────────────────────┘
            │
            ▼
   ┌─────────────────┐
   │   Local Storage │
   │                 │
   │  • User Files   │
   │  • Vector DB    │
   │  • Transcripts  │
   │  • (License — v1.1)
   └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (bundled in installer)
- **Node.js 18+** (bundled in installer)
- **Ollama** (auto-installed or manual setup)

### Installation

1. **Download Installer**
   - [macOS (Apple Silicon)](releases/privatixai-macos-arm64.dmg)
   - [macOS (Intel)](releases/privatixai-macos-x64.dmg)
   - [Windows](releases/privatixai-windows-x64.exe)
   - [Linux](releases/privatixai-linux-x64.AppImage)

2. **Run Installer**
   - Double-click and follow prompts
   - No additional setup required
   - App starts automatically

3. **First Launch**
   - Ollama setup wizard (if needed)
   - Upload your first document

### Development Setup

```bash
# Clone repository
git clone https://github.com/privatixai/privatixai.git
cd privatixai

# Backend setup
cd privatixai-be
pip install -r requirements.txt
cp config.env .env.local
uvicorn app:app --reload

# Frontend setup (new terminal)
cd ../privatixai-fe
npm install
npm run electron:dev
```

## 📖 Usage

### Basic Workflow

1. **Upload Files**: Drag & drop documents, audio, or video
2. **Wait for Processing**: Automatic transcription and indexing
3. **Ask Questions**: Chat with your knowledge base
4. **Get Cited Answers**: Responses include source references

### Example Queries

- *"What are the key points from my meeting recording?"*
- *"Summarize the PDF I uploaded about machine learning"*
- *"Find all mentions of 'budget' in my documents"*
- *"What did John say about the project timeline?"*

### Advanced Features

- **Memory Search**: Vector-based semantic search
- **Citation Tracking**: Every answer includes sources
- **Export Options**: Save conversations and findings
- **Batch Processing**: Upload multiple files at once

## 🛠️ Configuration

### Environment Variables

```bash
# Backend (.env.local)
DEBUG=false
USE_LOCAL_LLM=true
DEFAULT_LLM_MODEL=mistral
OLLAMA_BASE_URL=http://localhost:11434
MAX_FILE_SIZE_MB=100
```

### Ollama Models

```bash
# Install recommended models
ollama pull mistral
ollama pull llama3
ollama pull phi3
```

### Storage Locations

- **macOS**: `~/Library/Application Support/PrivatixAI/`
- **Windows**: `%APPDATA%/PrivatixAI/`
- **Linux**: `~/.local/share/PrivatixAI/`

## 🔧 Development

### Project Structure

```
privatixai/
├── privatixai-fe/          # Electron + React frontend
├── privatixai-be/          # FastAPI backend
├── docs/                   # Documentation
├── data/                   # User data (runtime)
└── README.md              # This file
```

### Key Technologies

- **Frontend**: Electron, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, Pydantic
- **AI Stack**: Ollama, Whisper, ChromaDB, SentenceTransformers
- **Storage**: Local file system, Vector DB

### Build & Package

```bash
# Development build
npm run build:dev

# Production build
npm run build:prod

# Package for distribution
npm run package:all
```

## 🔐 Privacy & Security

### Data Protection
- All processing happens on your device
- No data transmission to external servers
- Encrypted local storage for sensitive data
- Optional data export for backup

### Network Security
- Backend only binds to localhost (127.0.0.1)
- No outbound network connections in production
- CORS restricted to local origins only
- Optional offline mode for complete isolation

### License Model (planned for v1.1)
- Device-bound license validation
- Offline trial mode
- No license server required
- Local JSON-based license files

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](privatixai-be/docs/)
- [User Manual](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPMENT.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Code Standards

- **TypeScript**: Strict mode, explicit types
- **Python**: Type hints, Black formatting
- **Testing**: Unit tests for all business logic
- **Documentation**: Comments for complex operations

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/privatixai/privatixai/issues)
- **Documentation**: [Wiki](https://github.com/privatixai/privatixai/wiki)
- **Community**: [Discussions](https://github.com/privatixai/privatixai/discussions)
- **Official Website**: [https://privatixai.eu/](https://privatixai.eu/)

## 🗺️ Roadmap

### Version 0.1 (Current)
- ✅ Basic chat interface with AI assistant
- ✅ File upload (PDF, DOCX, TXT)
- ✅ Document processing and indexing
- ✅ Youtube Video (transcription) Ingestion
- ✅ Local AI model integration
- ✅ Memory of uploaded documents
- ✅ Question-answering from your files

### Version 1.0 (Next)
- 🔄 License management (device-bound, offline)
- 🔄 Advanced search across your documents
- 🔄 Upload multiple files at once
- 🔄 Save and export your conversations
- 🔄 Improved user interface and experience
- 🔄 Support for Windows and Linux
- 🔄 Better AI responses and accuracy
- 🔄 Option to use your own AI provider
- 🔄 Support for more file types:
  - Documents: MD, TXT
  - Audio: MP3, WAV, M4A, FLAC
  - Video: MP4, MOV, AVI (with transcription)
  - Subtitles: SRT, VTT, ASS

---

**PrivatixAI** - Your data, your device, your privacy. 🔒

**Visit [https://privatixai.eu/](https://privatixai.eu/) for more information.**
