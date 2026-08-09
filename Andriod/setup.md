# Termux & PRoot Ubuntu Setup Notes

## 1. Termux Base & SSH Setup
pkg install sshd
passwd
sshd

## 2. Useful References & Resources
- Video Tutorial: https://www.youtube.com/watch?v=zFI-Vb2bvSY
- GitHub Repository: https://github.com/AbuZar-Ansarii/Claude-Ollama-VScode (Claude portion skipped)

## 3. Running Local AI Models (Ollama)
- Start Ollama (in Termux):
  ollama run nemotron-3-super:cloud
- Exit Session: Press Ctrl + D or type /bye

## 4. PRoot Ubuntu & VS Code Server (code-server)
- Launch PRoot Ubuntu:
  proot-distro login ubuntu
- Run Code Server:
  code-server --auth none --bind-addr 0.0.0.0:9999

## 5. Global Git Configuration
install git setup SSH
git config --global user.name "Jing Cheng Xiaomi"
git config --global user.email "jingcheng070@gmail.com"

## 6. Install python
apt update && apt install -y python3