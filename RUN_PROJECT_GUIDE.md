# VI Nebula: Zero-Coding Run Guide

This guide is written for someone who has never coded before. Follow it slowly from top to bottom. You do not need to understand the code to run the project.

## 1. What This Project Is

VI Nebula is a local demo of a digital marketplace.

In simple words:

- The website is the shop screen you use in the browser.
- The backend is the engine that receives uploads, purchases, wallet balances, and blockchain data.
- The miner is a separate program that confirms pending uploads or purchases.
- The storage folders keep uploaded files after they are checked.

You will usually run three things:

1. Backend server
2. Frontend website
3. Miner

Each one runs in its own terminal window.

## 2. What You Need Installed

Install these first:

### Required

- Python 3.10 or newer
- Node.js 20 LTS or newer
- Git, optional but useful

### Needed For Full Mining Verification

- Docker Desktop

Docker is used when the miner checks code assets. For normal browsing and UI testing, Docker is not always needed. For full end-to-end verification, install it and keep Docker Desktop open.

## 3. Where The Project Is

Your project folder is:

```powershell
C:\Prototypes\VI_Nebula
```

Every command in this guide assumes you are inside that folder.

To open it:

1. Press `Windows`
2. Search `PowerShell`
3. Open PowerShell
4. Type:

```powershell
cd C:\Prototypes\VI_Nebula
```

## 4. First-Time Setup

Do this only the first time, or after deleting dependencies.

### Step 1: Create Python Environment

In PowerShell:

```powershell
cd C:\Prototypes\VI_Nebula
python -m venv .venv
```

### Step 2: Activate Python Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try activation again:

```powershell
.\.venv\Scripts\Activate.ps1
```

When it works, your terminal line should start with:

```text
(.venv)
```

### Step 3: Install Python Packages

```powershell
python -m pip install flask flask-cors cryptography docker pytest
```

### Step 4: Install Frontend Packages

```powershell
cd C:\Prototypes\VI_Nebula\frontend
npm install
```

Then go back to the main project folder:

```powershell
cd C:\Prototypes\VI_Nebula
```

## 5. Simple Run Mode For Development

Use this mode when you want to test the app while developing.

You need three PowerShell windows.

### Terminal 1: Start Backend

Open PowerShell:

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python app.py
```

Keep this window open.

Backend runs at:

```text
http://localhost:5000
```

### Terminal 2: Start Frontend Website

Open another PowerShell window:

```powershell
cd C:\Prototypes\VI_Nebula\frontend
npm run dev
```

Keep this window open.

Website runs at:

```text
http://localhost:3000
```

Open this in your browser:

```text
http://localhost:3000
```

### Terminal 3: Start Miner

Open a third PowerShell window:

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python miner.py
```

Keep this window open.

When the miner says to press Enter, press `Enter` whenever you want it to process pending uploads or purchases.

## 6. Full Single-Server Run Mode

Use this when you want the Flask backend to serve the already-built frontend.

### Step 1: Build The Website

```powershell
cd C:\Prototypes\VI_Nebula\frontend
npm run build
```

This creates:

```text
frontend\out
```

### Step 2: Start Backend

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python app.py
```

Then open:

```text
http://localhost:5000
```

In this mode, you do not need `npm run dev`.

## 7. How To Use The App End To End

### Step 1: Open Website

Use:

```text
http://localhost:3000
```

If you used full single-server mode, use:

```text
http://localhost:5000
```

### Step 2: Create Or Use Wallet

Use the app login/wallet screen. The wallet identifies the user inside the marketplace.

### Step 3: Claim Faucet Coins

Use the faucet option in the app if available. This gives test coins so you can buy assets.

The backend endpoint behind this is:

```text
POST /api/faucet
```

### Step 4: Upload An Asset

Use the sell/upload page.

Recommended beginner test files:

- A small `.png` image
- A small `.jpg` image
- A simple `.py` Python file

After upload, the asset goes into the mempool. That means it is waiting for miner confirmation.

### Step 5: Mine The Pending Upload

Go to the miner terminal and press:

```text
Enter
```

If mining succeeds, the asset becomes verified and appears in the marketplace state.

### Step 6: Buy An Asset

Use another wallet/user in the app, claim faucet coins, then buy the asset.

The purchase also waits in the mempool.

### Step 7: Mine The Pending Purchase

Go back to the miner terminal and press:

```text
Enter
```

After mining, ownership changes to the buyer.

### Step 8: Download The Asset

The owner can download the verified asset from the app.

## 8. Quick Health Checks

Use these links while the backend is running:

### Check Market State

Open:

```text
http://localhost:5000/api/market_state
```

You should see JSON text. JSON looks like structured text with `{ }`.

### Check Pending Transactions

Open:

```text
http://localhost:5000/api/mempool
```

If uploads or purchases are waiting, you will see them here.

### Check Blockchain

Open:

```text
http://localhost:5000/api/chain
```

This shows the chain blocks.

## 9. Important Ports

These are local addresses used by the project:

| Thing | Port | Address |
|---|---:|---|
| Frontend dev website | 3000 | `http://localhost:3000` |
| Backend API and built website | 5000 | `http://localhost:5000` |
| Gateway blockchain peer | 6000 | internal |
| Miner blockchain peer | 6001 | internal |

If one of these ports is already being used, close the old terminal running it or restart your computer.

## 10. Common Problems And Fixes

### Problem: `python` is not recognized

Python is not installed or not added to PATH.

Fix:

- Install Python from `https://www.python.org/downloads/`
- During install, tick `Add Python to PATH`
- Close and reopen PowerShell

### Problem: `npm` is not recognized

Node.js is not installed.

Fix:

- Install Node.js LTS from `https://nodejs.org/`
- Close and reopen PowerShell

### Problem: PowerShell blocks `.venv` activation

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Problem: Website says backend is unreachable

The frontend is open, but the backend is not running.

Fix:

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python app.py
```

### Problem: Backend says frontend build not found

You opened `http://localhost:5000`, but `frontend\out` does not exist yet.

Fix:

```powershell
cd C:\Prototypes\VI_Nebula\frontend
npm run build
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python app.py
```

Or use development mode and open:

```text
http://localhost:3000
```

### Problem: Miner says Docker is blocked or unavailable

Docker Desktop is not running, not installed, or not ready yet.

Fix:

1. Open Docker Desktop
2. Wait until it says Docker is running
3. Restart `python miner.py`

### Problem: Miner says mempool is empty

There is nothing waiting to process.

Fix:

- Upload an asset first, or make a purchase first
- Then press `Enter` in the miner window

### Problem: Port already in use

Another copy of the app is already running.

Fix:

- Close old PowerShell windows running this project
- Or restart the computer
- Then run the commands again

## 11. How To Stop The Project

Go to each PowerShell window and press:

```text
Ctrl + C
```

Do this for:

- Backend terminal
- Frontend terminal
- Miner terminal

## 12. Recommended VS Code Workflow

If you use VS Code:

1. Open VS Code
2. Click `File > Open Folder`
3. Select `C:\Prototypes\VI_Nebula`
4. Open three terminals inside VS Code using `Terminal > New Terminal`
5. Run backend, frontend, and miner in separate terminals

Recommended extensions:

- Python
- Pylance
- ESLint
- Tailwind CSS IntelliSense
- Docker

Useful AI assistant prompt:

```text
I am running VI Nebula locally on Windows. Explain any error I paste in simple steps. Do not rewrite the whole project. First identify whether the error belongs to Python backend, Next.js frontend, Docker, or the miner.
```

## 13. Fastest Daily Start

After setup is already done, use only these commands.

### Terminal 1

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python app.py
```

### Terminal 2

```powershell
cd C:\Prototypes\VI_Nebula\frontend
npm run dev
```

### Terminal 3

```powershell
cd C:\Prototypes\VI_Nebula
.\.venv\Scripts\Activate.ps1
python miner.py
```

Open:

```text
http://localhost:3000
```

