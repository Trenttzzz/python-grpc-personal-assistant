# gRPC Text Analyzer with Multiple Communication Patterns

A comprehensive gRPC-based text analyzer application that demonstrates all four gRPC communication patterns using the Groq API to process and respond to user messages.

## Project Overview

This project implements a client-server architecture using gRPC for communication, showcasing:

1. **Unary RPC** - Simple question answering and URL summarization
2. **Server Streaming RPC** - Stream chatbot responses in parts
3. **Client Streaming RPC** - Send multiple URLs to summarize in bulk
4. **Bidirectional Streaming RPC** - Real-time chatbot with message history

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- A Groq API key (sign up at [groq.com](https://console.groq.com) if you don't have one)

## Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd grpc-text-analyzer
   ```

2. Install the required packages (using virtual env recommended):
   ```
   pip install grpcio grpcio-tools groq
   ```

3. Set your Groq API key as an environment variable:
   ```
   export GROQ_API_KEY=your_api_key_here
   ```
   
   For Windows users (Command Prompt):
   ```
   set GROQ_API_KEY=your_api_key_here
   ```
   
   For Windows users (PowerShell):
   ```
   $env:GROQ_API_KEY="your_api_key_here"
   ```

4. Generate the gRPC code from the proto file:
   ```
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chatbot.proto
   ```

## Running the Application

1. Start the server:
   ```
   python server.py
   ```

2. In a separate terminal, start the client:
   ```
   python client.py
   ```

3. Choose from the menu which gRPC communication pattern you want to use:
   - Option 1: Unary RPC - Simple question answering
   - Option 2: Server Streaming RPC - See responses arrive in chunks
   - Option 3: Client Streaming RPC - Submit multiple URLs for summarization
   - Option 4: Bidirectional Streaming RPC - Interactive chat session with history

4. Follow the prompts to interact with each communication pattern.

5. Use 'quit' to return to the main menu or exit the application.

## Features

- **Unary RPC**: Standard question-answering with single request and response
- **Server Streaming RPC**: The server breaks down the AI's response into chunks and streams them to the client
- **Client Streaming RPC**: The client sends multiple URLs to be summarized in a single session
- **Bidirectional Streaming RPC**: Real-time chat with message history, allowing complex conversation contexts

## Technical Implementation

- **Protocol Buffers**: Defines the service interface and message types
- **gRPC**: Handles communication between client and server
- **Groq API**: Powers the AI text generation capabilities
- **Multithreading**: Used for bidirectional streaming to handle concurrent message sending and receiving

## Project Structure

- `chatbot.proto`: Defines the gRPC service and message types for all four communication patterns
- `chatbot_pb2.py` and `chatbot_pb2_grpc.py`: Generated gRPC code
- `server.py`: Implements the gRPC server with handlers for all four RPC types
- `client.py`: Interactive client with menu-based selection of RPC patterns

## Notes

- The server uses an insecure channel for simplicity. In a production environment, secure channels should be implemented.
- For the client streaming URL summarization, the system doesn't actually fetch the URL content (only simulates it)
- The bidirectional streaming maintains conversation history for more contextual responses