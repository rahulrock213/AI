#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science dvisvgm
pip install -r requirements.txt
echo "Setup complete. Try: python make_video.py quizzes/bat_and_ball.json"
