## Overview

**FileMaster CLI** is a robust command-line interface designed for efficient file management across local and remote systems. It provides a suite of commands to manage files and directories with ease, supporting operations such as create, read, update, delete, move, copy, and search. This documentation outlines all available commands, request/response formats, authentication mechanisms, and deployment instructions.

---

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Commands](#commands)
  - [List Files (`ls`)](#list-files-ls)
  - [Create Directory (`mkdir`)](#create-directory-mkdir)
  - [Create File (`touch`)](#create-file-touch)
  - [Read File (`cat`)](#read-file-cat)
  - [Copy File/Directory (`cp`)](#copy-filedirectory-cp)
  - [Move/Rename (`mv`)](#moverename-mv)
  - [Delete (`rm`)](#delete-rm)
  - [Search Files (`find`)](#search-files-find)
  - [File Info (`info`)](#file-info-info)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Deployment Guide](#deployment-guide)
- [Support](#support)

---

### Prerequisites

- Python 3.8 or higher
- `pip` package manager

### Install via pip

pip install filemaster-cli

### Verify Installation

filemaster --version

Expected output:
FileMaster CLI v1.2.0

---

## Authentication

FileMaster CLI supports secure access to remote storage systems (e.g., S3, Google Cloud Storage) via authentication tokens.

### Configuration

Run the setup command to configure credentials:

filemaster configure

You will be prompted to enter:

- **Provider**: `aws`, `gcp`, `azure`, or `local`
- **Access Key ID** (for cloud providers)
- **Secret Access Key**
- **Region** (if applicable)
- **Default Path/Endpoint**

Credentials are stored encrypted in `~/.filemaster/config.json`.

### Environment Variables (Alternative)

Set environment variables:

export FILEMASTER_PROVIDER=aws
export FILEMASTER_ACCESS_KEY=your_access_key
export FILEMASTER_SECRET_KEY=your_secret_key
export FILEMASTER_REGION=us-east-1

> **Note**: Environment variables override config file settings.

---

### List Files (`ls`)

Lists files and directories in a specified path.

#### Syntax

filemaster ls [PATH] [OPTIONS]

#### Options

| Option | Description |
|--------|-------------|
| `-l`   | Long format (permissions, size, modified date) |
| `-r`   | Recursive listing |
| `--hidden` | Include hidden files |

#### Example Request

filemaster ls /home/user/docs -l

#### Example Response

-rw-r--r-- 2048 2023-10-05 14:23 report.pdf
drwxr-xr-x 4096 2023-09-12 09:15 projects/
-rw-r--r-- 1024 2023-10-01 11:05 notes.txt

---

### Create Directory (`mkdir`)

Creates a new directory.

#### Syntax

filemaster mkdir PATH [OPTIONS]

#### Options

| Option | Description |
|--------|-------------|
| `-p`   | Create parent directories as needed |

#### Example Request

filemaster mkdir /home/user/new-project/src -p

#### Example Response

Directory created: /home/user/new-project/src

---

### Create File (`touch`)

Creates an empty file or updates the timestamp of an existing file.

#### Syntax

filemaster touch PATH

#### Example Request

filemaster touch /home/user/notes/todo.txt

#### Example Response

File created: /home/user/notes/todo.txt

---

### Read File (`cat`)

Outputs the contents of a file to stdout.

#### Example Request

filemaster cat /home/user/config.json

#### Example Response

{
  "theme": "dark",
  "auto_save": true,
  "language": "en"
}

---

### Copy File/Directory (`cp`)

Copies files or directories.

#### Syntax

filemaster cp SOURCE DEST [OPTIONS]

#### Options

| Option | Description |
|--------|-------------|
| `-r`   | Copy directories recursively |
| `--force` | Overwrite destination if exists |

#### Example Request

filemaster cp /home/user/file.txt /backup/ --force

#### Example Response

Copied: /home/user/file.txt → /backup/file.txt

---

### Move/Rename (`mv`)

Moves or renames a file or directory.

#### Syntax

filemaster mv SOURCE DEST

#### Example Request

filemaster mv /home/user/old-name.txt /home/user/new-name.txt

#### Example Response

Moved: /home/user/old-name.txt → /home/user/new-name.txt

---

### Delete (`rm`)

Deletes files or directories.

#### Syntax

filemaster rm PATH [OPTIONS]

#### Options

| Option | Description |
|--------|-------------|
| `-r`   | Remove directories and their contents recursively |
| `--force` | Ignore nonexistent files, never prompt |

#### Example Request

filemaster rm /tmp/temp-file.log --force

#### Example Response

Deleted: /tmp/temp-file.log

---

### Search Files (`find`)

Searches for files matching a pattern.

#### Syntax

filemaster find PATH -name PATTERN [OPTIONS]

#### Options

| Option | Description |
|--------|-------------|
| `-type f` | Only files |
| `-type d` | Only directories |
| `-size +N` | Files larger than N KB |
| `-mtime -N` | Modified in the last N days |

#### Example Request

filemaster find /home/user -name "*.log" -mtime -7

#### Example Response

/home/user/app.log
/home/user/debug.log

---

### File Info (`info`)

Displays detailed metadata about a file or directory.

#### Syntax

filemaster info PATH

#### Example Request

filemaster info /home/user/report.pdf

#### Example Response

{
  "path": "/home/user/report.pdf",
  "type": "file",
  "size": 2048,
  "permissions": "rw-r--r--",
  "owner": "user",
  "created": "2023-09-20T10:15:30Z",
  "modified": "2023-10-05T14:23:12Z",
  "checksum": "a1b2c3d4e5f6..."
}

---

### Example 1: Recursive Copy with Authentication

filemaster cp s3://mybucket/data/ /local/data/ -r

> Prompts for AWS credentials if not configured.

**Response:**
Copied: s3://mybucket/data/file1.csv → /local/data/file1.csv
Copied: s3://mybucket/data/file2.csv → /local/data/file2.csv
Copy completed: 2 files

### Example 2: Search Large Files

filemaster find /home/user -type f -size +10240

**Response:**
/home/user/videos/demo.mp4 (12450 KB)
/home/user/archive.zip (15670 KB)

---

## Error Handling

FileMaster CLI returns structured error messages with exit codes.

| Exit Code | Meaning |
|---------|--------|
| `1`     | General error |
| `2`     | Authentication failed |
| `3`     | File or directory not found |
| `4`     | Permission denied |
| `5`     | Invalid arguments |

### Example Error Output

filemaster cat /root/secret.txt

**Response:**
Error: Permission denied (code: 4)
Path: /root/secret.txt
Action: Read operation not allowed

---

### Local Deployment

1. Install via pip:
      pip install filemaster-cli
   
2. Configure credentials:
      filemaster configure
   
3. Test connection:
      filemaster ls ~
   
### Docker Deployment

Build and run in a container:

Dockerfile
FROM python:3.9-slim

RUN pip install filemaster-cli

COPY config.json /root/.filemaster/config.json

ENTRYPOINT ["filemaster"]

Build image:
docker build -t filemaster .

Run container:
docker run -v /host/data:/data filemaster ls /data

### CI/CD Integration

Use in GitHub Actions:

- name: Install FileMaster CLI
  run: pip install filemaster-cli

- name: Deploy files
  run: |
    filemaster configure --provider aws --key ${{ secrets.AWS_KEY }} --secret ${{ secrets.AWS_SECRET }}
    filemaster cp ./dist s3://myapp/releases/v1.2.0 -r

---

## Support

For issues and feature requests:

- GitHub: [https://github.com/example/filemaster-cli](https://github.com/example/filemaster-cli)
- Email: support@filemaster.dev
- CLI Help: `filemaster --help`

---

> **Note**: Always keep your access keys secure. Never commit credentials to version control.