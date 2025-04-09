# gRPC Personal Assistant

A simple gRPC-based chatbot application that uses the Groq API to process and respond to user messages.

## Project Overview

This project implements a client-server architecture using gRPC for communication:

- The client provides a simple command-line interface for interacting with the AI assistant.
- The server processes user messages by sending them to the Groq API and returning the AI-generated responses.
- Communication between client and server is handled via gRPC protocol buffers.

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

2. Install the required packages:
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

4. (Optional) If you need to regenerate the gRPC code from the proto file:
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

3. Interact with the AI assistant through the client terminal. Type your messages and receive AI-generated responses.

4. To exit the client, type `quit`, `exit`, or `bye`.

## Features

- Real-time interaction with an AI assistant
- Powered by Groq's LLaMA 3.1 model
- Simple command-line interface
- Robust error handling

## Project Structure

- `chatbot.proto`: Defines the gRPC service and message types
- `chatbot_pb2.py` and `chatbot_pb2_grpc.py`: Generated gRPC code
- `server.py`: Implements the gRPC server and handles Groq API calls
- `client.py`: Implements the gRPC client and user interface

## Notes

- The server uses an insecure channel for simplicity. In a production environment, secure channels should be implemented.
- Currently, the web_access feature defined in the proto file is not fully implemented.