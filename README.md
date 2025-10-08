# Document Extraction using AI

## Quick Guide

- Start Training Process

```sh
# 1. Start docker compose project
docker compose -f docker-compose.train.yml up -d

# 2. Create label studio projects
# Open Label Studio at 'localhost:8080' and login to your account.
# Email/Password: gif@label.studio/gif@hackaithon
# Go to 'localhost:8080/user/account' and scroll to the bottom.
# Press 'Create New Token', then 'Copy' it.
docker compose -f docker-compose.train.yml exec label-studio python /label-studio/config/init.py -t "your-copied-token"
```