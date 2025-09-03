# OWUI_File_Gen_Export – Export Files Directly from Open WebUI

A lightweight, MCPO-integrated tool that lets you **generate and export real files** (PDF, Excel, ZIP, etc.) directly from Open WebUI — just like ChatGPT or Claude.

✅ Supports both **Python** and **Docker**  
✅ Fully configurable  
✅ Ready for production workflows  
✅ Open source & MIT licensed

---

🚀 **Create and export files easily from Open WebUI!**

This tool allows seamless file generation and export directly from your Open WebUI environment using Python and FastAPI.

## Multi files

https://github.com/user-attachments/assets/41dadef9-7981-4439-bf5f-3b82fcbaff04


## Single archive

https://github.com/user-attachments/assets/1e70a977-62f1-498c-895c-7db135ded95b


# 🚀 Quick Start

### 🔧 For Python Users

1. Clone the repo:
   ```bash
   git clone https://github.com/GlisseManTV/OWUI_File_Gen_Export.git
   ```

2. Update env variables in `config.json`:
  These ones only concerns the MCPO part

   - `PYTHONPATH`: Path to your `LLM_Export` folder (e.g., `C:\temp\LLM_Export`) <=== MANDATORY no default value
   - `FILE_EXPORT_BASE_URL`: URL of your file export server (default is `http://localhost:9003/files`)
   - `FILE_EXPORT_DIR`: Directory where files will be saved (must match the server's export directory) (default is `PYTHONPATH\output`)
   - `PERSISTENT_FILES`: Set to `true` to keep files after download, `false` to delete after delay (default is false)
   - `FILES_DELAY`: Delay in minut to wait before checking for new files (default is 60)

3. Install dependencies:
   ```bash
   pip install openpyxl reportlab py7zr fastapi uvicorn python-multipart mcp
   ```

4. Run the file server:
   ```bat
   set FILE_EXPORT_DIR=C:\temp\LLM_Export\output
   start "File Export Server" python "YourPATH/LLM_Export/tools/file_export_server.py"
   ```

5. Use it in Open WebUI — your AI can now generate and export files in real time!

---

### PYTHON EXAMPLE
This file only concerns the MCPO part, you need to run the file server separately as shown above
This is an example of a minimal `config.json` for MCPO to enable file export but you can add other (or to other) MCP servers as needed.

```config.json
{
  "mcpServers": {
		"file_export": {
			"command": "python",
			"args": [
				"-m",
				"tools.file_export_mcp"
			],
			"env": {
				"PYTHONPATH": "C:\\temp\\LLM_Export", <==== HERE set the path to your LLM_Export folder (this one is Mandatory)
				"FILE_EXPORT_BASE_URL": "http://localhost:9003/files", <==== HERE set the URL of your file export server
				"FILE_EXPORT_DIR": "C:\\temp\\LLM_Export\\output", <==== HERE set the directory where files will be saved (must match the server's export directory)
				"PERSISTENT_FILES": "false", <==== HERE set to true to keep files after download, false to delete after delay
				"FILES_DELAY": "60" <==== HERE set the delay in minut to wait before checking for new files
			},
			"disabled": false,
			"autoApprove": []
		}
}

```

---

## 🐳 For Docker User (Recommended)

Use 
```
docker pull ghcr.io/glissemantv/owui-file-export-server:dev-latest
docker pull ghcr.io/glissemantv/owui-mcpo:dev-latest
```

### 🛠️ DOCKER ENV VARIABLES

For OWUI-MCPO
   - `MCPO_API_KEY`: Your MCPO API key (no default value, not mandatory but advised)
   - `FILE_EXPORT_BASE_URL`: URL of your file export server (default is `http://localhost:9003/files`)
   - `FILE_EXPORT_DIR`: Directory where files will be saved (must match the server's export directory) (default is `/output`) path must be mounted as a volume
   - `PERSISTENT_FILES`: Set to `true` to keep files after download, `false` to delete after delay (default is `false`)
   - `FILES_DELAY`: Delay in minut to wait before checking for new files (default is 60)

For OWUI-FILE-EXPORT-SERVER
   - `FILE_EXPORT_DIR`: Directory where files will be saved (must match the MCPO's export directory) (default is `/output`) path must be mounted as a volume

> ✅ This ensures MCPO can correctly reach the file export server.
> ❌ If not set, file export will fail with a 404 or connection error.

---

### DOCKER EXAMPLE


Here is an example of a docker run script file to run both the file export server and the MCPO server:
```
docker run -d --name file-export-server --network host -e FILE_EXPORT_DIR=/data/output -p 9003:9003 -v /path/to/your/export/folder:/data/output ghcr.io/glissemantv/owui-file-export-server:latest
docker run -d --name owui-mcpo --network host -e FILE_EXPORT_BASE_URL=http://192.168.0.100:9003/files -e FILE_EXPORT_DIR=/output -e MCPO_API_KEY=top-secret -e PERSISTENT_FILES=True -e FILES_DELAY=1 -p 8000:8000 -v /path/to/your/export/folder:/output ghcr.io/glissemantv/owui-mcpo:latest
```

Here is an example of a `docker-compose.yaml` file to run both the file export server and the MCPO server:
```yaml
services:
  file-export-server:
    image: ghcr.io/glissemantv/owui-file-export-server:latest
    container_name: file-export-server
    environment:
      - EXPORT_DIR=/data/output
    ports:
      - "9003:9003"
    volumes:
      - /your/export-data:/data/output

  owui-mcpo:
    image: ghcr.io/glissemantv/owui-mcpo:latest
    container_name: owui-mcpo
    environment:
      - FILE_EXPORT_BASE_URL=http://file-export-server:9003/files
      - FILE_EXPORT_DIR=/output
      - MCPO_API_KEY=top-secret
      - FILES_DELAY=1
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    volumes:
      - /your/export-data:/output
    depends_on:
      - file-export-server
```
---

## 📦 Supported File Types

- ✅ `.xlsx` (Excel)
- ✅ `.pdf` (PDF)
- ✅ `.csv` (CSV)
- ✅ `.zip` and `.7z` (Archives)
- ✅ Any other file type 

---

## 📂 Project Structure

```
OWUI_File_Gen_Export/
├── LLM_Export/
│   ├── tools/
│   │   ├── file_export_server.py
│   │   └── file_export_mcp.py
│   └── ...
├── docker/
│   ├── file_server/
│   │   ├── Dockerfile.server
│   │   ├── file_server_compose.yaml
│   │   └── file_export_server.py
│   └── mcpo/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── config.json
│       ├── MCPO_server_compose.yaml
│       └──tools/
│           └── file_export_mcp.py
└── README.md
```

---

## 📌 Notes

- File output paths must match between `file_server` and `MCPO`
- Always use **absolute paths** for volume mounts
  
⚠️Some users are experiencing trouble with the MCPO server, please use this fix⚠️
```config.json
{
  "mcpServers": {
		"file_export": {
			"command": "python", <==== HERE change "python" to "python3", "python3.11" or "python3.12"
			"args": [
				"-m",
				"tools.file_export_mcp"
			],
			"env": {
				"PYTHONPATH": "C:\\temp\\LLM_Export" <==== HERE set the path to your LLM_Export folder (this one is Mandatory)
			},
			"disabled": false,
			"autoApprove": []
		}
}

```
---

## 🌟 Why This Matters

This tool turns Open WebUI into a **true productivity engine** — where AI doesn’t just chat, but **delivers usable, downloadable files**.

---

## 📄 License

MIT License – Feel free to use, modify, and distribute.

---

📬 **Need help?** Open an issue or start a discussion on GitHub!

