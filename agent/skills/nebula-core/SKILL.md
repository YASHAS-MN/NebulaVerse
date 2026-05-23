---
name: nebula-core-architect
description: Expert skill for building the 3-layer Nebula Decentralized Software Marketplace. Handles Blockchain logic, P2P networking, and Docker-based sandboxing.
---

# Skill: Nebula Core Architect

## Goal
To architect and implement a functional prototype of the Nebula Marketplace, ensuring strict isolation between the Centralized Storefront (Layer 1) and the Decentralized Protocol (Layer 2) using the Bridge (Layer 3).

## Instructions

### 1. Layer 1: Storefront (React)
- **Framework**: Use React with Vite for speed.
- **State Management**: Use local state or Context API for the prototype.
- **UI Logic**: Focus on the "Marketplace Dashboard" and "Wallet View."
- **Communication**: All data must be fetched from the Layer 3 API (Flask), never directly from the Blockchain node.

### 2. Layer 2: Core Protocol (Python P2P)
- **Ledger**: Implement a `Blockchain` class with SHA-256 and Proof-of-Work.
- **P2P**: Use Python `socket` to implement a simple discovery protocol. Hardcode `SEED_NODES` for peer discovery.
- **Sandbox (CRITICAL)**: 
    - Use `docker-py` (Docker SDK for Python).
    - Every uploaded file must be run in a container with `network_disabled=True`.
    - Limit resource usage: `mem_limit='128m'`, `cpu_period=100000`, `cpu_quota=50000`.
    - Verification: Capture STDOUT/STDERR. If the code executes successfully without a timeout, return a "Passed" signature.

### 3. Layer 3: The Bridge (Flask API)
- **Endpoint 1**: `/get_assets` - Fetches validated software from the local node's ledger.
- **Endpoint 2**: `/purchase` - Initiates the Escrow logic.
- **Endpoint 3**: `/mine` - Triggers the local mining/sandboxing process.

## Constraints & Safety Rules
- **DO NOT** execute any user-provided code on the host machine. Everything must go through the Docker Sandbox.
- **DO NOT** hardcode Private Keys. Use a `.env` file for all sensitive data.
- **NO CENTRAL SERVER**: Ensure the P2P logic allows the app to work even if the primary PC is offline (after initial peer discovery).

## Example Commands
- "Nebula: Generate a new Block class with a difficulty adjustment algorithm."
- "Nebula: Create the Docker execution script that handles .py file verification."
- "Nebula: Build the React component for the Seller's upload form."